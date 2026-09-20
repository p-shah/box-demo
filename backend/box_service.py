"""
Box service layer for the Secure Client Reporting Portal demo.

Wraps box-sdk-gen calls used by the Flask API: folder/document listing,
upload + metadata classification, Box AI (summary + structured extraction),
and scoped shared links. Mirrors the flow in ../box_secure_portal_demo.py
but exposed over HTTP for the custom React front end instead of a script.
"""

import datetime
import os
import threading
import uuid

from box_sdk_gen import (
    BoxClient,
    BoxDeveloperTokenAuth,
    CreateFolderParent,
    UpdateFileByIdParent,
    UploadFileAttributes,
    UploadFileAttributesParentField,
    AddShareLinkToFileSharedLink,
    AddShareLinkToFileSharedLinkAccessField,
    AddShareLinkToFileSharedLinkPermissionsField,
    CreateFileMetadataByIdScope,
    GetFileMetadataByIdScope,
    CreateAiAskMode,
    AiItemAsk,
    AiItemAskTypeField,
    AiItemBase,
    CreateAiExtractStructuredFields,
)
from box_sdk_gen.box.errors import BoxSDKError

METADATA_TEMPLATE_KEY = "clientReportInfo"
PORTAL_ROOT_FOLDER_ID = os.environ.get("BOX_PORTAL_ROOT_FOLDER_ID", "418113709484")

_SUMMARY_PROMPT = (
    "You are briefing a wealth management advisor before a client call. "
    "In 3-4 short bullet points, summarize this statement: overall performance "
    "this period, the biggest driver of the change, and anything the advisor "
    "should flag to the client. Be concise and use plain English, no jargon."
)

_MULTI_SUMMARY_PROMPT = (
    "You are briefing a wealth management advisor before a client call, using "
    "multiple statements for the same client. In 4-6 short bullet points, "
    "summarize what changed across these periods: the overall trend, the "
    "biggest driver of that trend, and anything the advisor should flag to "
    "the client. Reference specific periods where it's relevant. Be concise "
    "and use plain English, no jargon."
)

_CLASSIFICATION_FIELDS = [
    CreateAiExtractStructuredFields(
        key="clientName",
        display_name="Client Name",
        prompt=(
            "The name of the client, account holder, or trust this statement was "
            "prepared for — typically after a label like 'Prepared for:'. Return "
            "just the name, no titles, account numbers, or salutations."
        ),
    ),
    CreateAiExtractStructuredFields(
        key="quarter",
        display_name="Quarter",
        prompt=(
            "The reporting period this statement covers, formatted exactly as "
            "'Q<1-4>-<4 digit year>', e.g. 'Q3-2026'. Infer it from the statement's "
            "period heading or date range, not from the file name."
        ),
    ),
]

UNSORTED_CLIENT_NAME = "Unsorted"

_HIGHLIGHT_FIELDS = [
    CreateAiExtractStructuredFields(
        key="beginningValue",
        display_name="Beginning Value",
        prompt="The account's beginning/starting value for the period, as a currency string.",
    ),
    CreateAiExtractStructuredFields(
        key="endingValue",
        display_name="Ending Value",
        prompt="The account's ending value for the period, as a currency string.",
    ),
    CreateAiExtractStructuredFields(
        key="netMarketGain",
        display_name="Net Market Gain/Loss",
        prompt="The net market gain or loss for the period, as a currency string.",
    ),
    CreateAiExtractStructuredFields(
        key="topHolding",
        display_name="Largest Holding",
        prompt="The name of the largest holding in the account by market value.",
    ),
    CreateAiExtractStructuredFields(
        key="performanceDriver",
        display_name="Performance Driver",
        prompt="In one short sentence, the main driver of performance this period.",
    ),
]

_MULTI_HIGHLIGHT_FIELDS = [
    CreateAiExtractStructuredFields(
        key="beginningValue",
        display_name="Beginning Value",
        prompt="The beginning/starting value from the EARLIEST-dated statement provided, as a currency string.",
    ),
    CreateAiExtractStructuredFields(
        key="endingValue",
        display_name="Ending Value",
        prompt="The ending value from the MOST RECENT statement provided, as a currency string.",
    ),
    CreateAiExtractStructuredFields(
        key="netMarketGain",
        display_name="Net Market Gain/Loss",
        prompt="The combined net market gain or loss across all statements provided, as a currency string.",
    ),
    CreateAiExtractStructuredFields(
        key="topHolding",
        display_name="Largest Holding",
        prompt="The largest holding by market value in the most recent statement provided.",
    ),
    CreateAiExtractStructuredFields(
        key="performanceDriver",
        display_name="Performance Driver",
        prompt="In one short sentence, the primary driver of performance across the statements provided.",
    ),
]

# In-memory activity log standing in for the "admin console" audit story.
# A real deployment would read this from Box's Events API instead.
_activity_log = []
_activity_lock = threading.Lock()


def log_action(client_name: str, file_name: str, action: str):
    entry = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "client": client_name,
        "file": file_name,
        "action": action,
    }
    with _activity_lock:
        _activity_log.insert(0, entry)
        del _activity_log[200:]
    return entry


def get_activity_log(limit: int = 50):
    with _activity_lock:
        return list(_activity_log[:limit])


_client_lock = threading.Lock()
_client = None


def get_client() -> BoxClient:
    global _client
    with _client_lock:
        if _client is None:
            token = os.environ.get("BOX_DEVELOPER_TOKEN")
            if not token:
                raise RuntimeError(
                    "Set BOX_DEVELOPER_TOKEN before running the backend. "
                    "Developer tokens expire after 60 minutes and must be "
                    "regenerated from the Box developer console."
                )
            auth = BoxDeveloperTokenAuth(token=token)
            _client = BoxClient(auth=auth)
        return _client


def _serialize_metadata(metadata) -> dict:
    if metadata is None:
        return {}
    # MetadataFull stashes any field not in its declared schema (i.e. every
    # custom template field, like reportType/quarter) in .extra_data.
    return dict(metadata.extra_data or {})


def list_clients() -> list:
    client = get_client()
    items = client.folders.get_folder_items(PORTAL_ROOT_FOLDER_ID, fields=["name", "type"])
    return [
        {"id": entry.id, "name": entry.name}
        for entry in items.entries
        if entry.type.value == "folder"
    ]


def _find_client_folder(client_name: str):
    client = get_client()
    items = client.folders.get_folder_items(PORTAL_ROOT_FOLDER_ID, fields=["name", "type"])
    needle = client_name.strip().lower()
    for entry in items.entries:
        if entry.type.value == "folder" and entry.name.strip().lower() == needle:
            return {"id": entry.id, "name": entry.name}
    return None


def resolve_client_folder(client_name: str) -> dict:
    """
    Finds the existing client folder matching this name (case-insensitive),
    or creates one — so an upload never has to wait on someone provisioning
    a folder first.
    """
    client = get_client()
    existing = _find_client_folder(client_name)
    if existing:
        return {**existing, "isNew": False}
    folder = client.folders.create_folder(
        client_name, CreateFolderParent(id=PORTAL_ROOT_FOLDER_ID)
    )
    return {"id": folder.id, "name": folder.name, "isNew": True}


def list_documents(folder_id: str) -> list:
    client = get_client()
    items = client.folders.get_folder_items(
        folder_id, fields=["name", "type", "size", "created_at"]
    )
    documents = []
    for entry in items.entries:
        if entry.type.value != "file":
            continue
        metadata = {}
        try:
            raw = client.file_metadata.get_file_metadata_by_id(
                entry.id, GetFileMetadataByIdScope.ENTERPRISE, METADATA_TEMPLATE_KEY
            )
            metadata = _serialize_metadata(raw)
        except BoxSDKError:
            pass
        documents.append(
            {
                "id": entry.id,
                "name": entry.name,
                "size": entry.size,
                # created_at isn't a declared field on the mini file schema, so
                # it comes back as the raw ISO 8601 string Box returns, unparsed.
                "createdAt": getattr(entry, "created_at", None),
                "metadata": metadata,
            }
        )
    return documents


def classify_document(file_id: str) -> dict:
    """
    Reads the uploaded statement with Box AI to determine who it's for and
    which quarter it covers, instead of relying on the uploader to know (or
    correctly type) either one.
    """
    client = get_client()
    try:
        response = client.ai.create_ai_extract_structured(
            items=[AiItemBase(id=file_id)],
            fields=_CLASSIFICATION_FIELDS,
        )
        answer = response.answer or {}
    except BoxSDKError:
        answer = {}
    return {
        "clientName": (answer.get("clientName") or "").strip(),
        "quarter": (answer.get("quarter") or "").strip(),
    }


def _next_available_name(client: BoxClient, folder_id: str, desired_name: str) -> str:
    items = client.folders.get_folder_items(folder_id, fields=["name", "type"])
    taken = {entry.name for entry in items.entries if entry.type.value == "file"}
    if desired_name not in taken:
        return desired_name
    stem, dot, ext = desired_name.rpartition(".")
    stem, ext = (stem, f".{ext}") if dot else (desired_name, "")
    n = 2
    while f"{stem} ({n}){ext}" in taken:
        n += 1
    return f"{stem} ({n}){ext}"


def upload_document(file_stream, file_name: str, report_type: str, sensitivity: str) -> dict:
    client = get_client()

    # Box AI can only read a file once it's actually in Box, so the client
    # can't be known yet — stage the upload at the portal root under a
    # collision-proof name and move it into place once classification tells
    # us where it belongs.
    staging_name = f"{uuid.uuid4().hex[:10]}_{file_name}"
    attributes = UploadFileAttributes(
        name=staging_name, parent=UploadFileAttributesParentField(id=PORTAL_ROOT_FOLDER_ID)
    )
    uploaded = client.uploads.upload_file(attributes, file_stream).entries[0]
    log_action(UNSORTED_CLIENT_NAME, file_name, "Statement uploaded, pending classification")

    try:
        classification = classify_document(uploaded.id)
        quarter = classification["quarter"] or "Unspecified"
        client_name = classification["clientName"] or UNSORTED_CLIENT_NAME

        if classification["quarter"]:
            log_action(client_name, file_name, f"Box AI detected reporting period: {quarter}")
        else:
            log_action(client_name, file_name, "Box AI could not determine a reporting period")

        folder_info = resolve_client_folder(client_name)
        if folder_info["isNew"]:
            log_action(folder_info["name"], file_name, "Box AI found no matching client — new folder created")
        else:
            log_action(folder_info["name"], file_name, "Box AI matched statement to existing client")

        # Restore the original (or de-duplicated, if the client folder
        # already has a same-named file) name as part of the move.
        final_name = _next_available_name(client, folder_info["id"], file_name)
        client.files.update_file_by_id(
            uploaded.id, name=final_name, parent=UpdateFileByIdParent(id=folder_info["id"])
        )
    except BoxSDKError:
        # Don't leave an unclassified orphan sitting in the portal root.
        try:
            client.files.delete_file_by_id(uploaded.id)
        except BoxSDKError:
            pass
        raise

    metadata_body = {
        "reportType": report_type,
        "quarter": quarter,
        "sensitivity": sensitivity,
        "generatedOn": datetime.date.today().isoformat(),
    }
    client.file_metadata.create_file_metadata_by_id(
        uploaded.id,
        CreateFileMetadataByIdScope.ENTERPRISE,
        METADATA_TEMPLATE_KEY,
        metadata_body,
    )
    log_action(folder_info["name"], final_name, "Metadata applied — Shield classification triggered")

    return {
        "id": uploaded.id,
        "name": final_name,
        "metadata": metadata_body,
        "client": {
            "id": folder_info["id"],
            "name": folder_info["name"],
            "isNew": folder_info["isNew"],
        },
    }


def _label(file_names: list) -> str:
    return file_names[0] if len(file_names) == 1 else f"{len(file_names)} statements"


def get_ai_summary(file_ids: list, file_names: list, client_name: str) -> dict:
    client = get_client()
    multi = len(file_ids) > 1
    response = client.ai.create_ai_ask(
        mode=CreateAiAskMode.MULTIPLE_ITEM_QA if multi else CreateAiAskMode.SINGLE_ITEM_QA,
        prompt=_MULTI_SUMMARY_PROMPT if multi else _SUMMARY_PROMPT,
        items=[AiItemAsk(id=fid, type=AiItemAskTypeField.FILE) for fid in file_ids],
        include_citations=True,
    )
    log_action(client_name, _label(file_names), "Box AI summary generated")
    citations = [
        {"content": c.content, "name": c.name} for c in (response.citations or [])
    ] if getattr(response, "citations", None) else []
    return {"summary": response.answer, "citations": citations}


def get_ai_highlights(file_ids: list, file_names: list, client_name: str) -> dict:
    client = get_client()
    multi = len(file_ids) > 1
    response = client.ai.create_ai_extract_structured(
        items=[AiItemBase(id=fid) for fid in file_ids],
        fields=_MULTI_HIGHLIGHT_FIELDS if multi else _HIGHLIGHT_FIELDS,
    )
    log_action(client_name, _label(file_names), "Box AI structured extraction generated")
    return dict(response.answer or {})


def create_shared_link(file_id: str, file_name: str, client_name: str, days_valid: int = 14) -> dict:
    client = get_client()
    expires_at = (
        datetime.datetime.utcnow() + datetime.timedelta(days=days_valid)
    ).isoformat() + "Z"
    result = client.shared_links_files.add_share_link_to_file(
        file_id,
        fields="shared_link",
        shared_link=AddShareLinkToFileSharedLink(
            access=AddShareLinkToFileSharedLinkAccessField.OPEN,
            unshared_at=expires_at,
            permissions=AddShareLinkToFileSharedLinkPermissionsField(can_download=False),
        ),
    )
    log_action(client_name, file_name, "Secure shared link created (view-only, expires in %d days)" % days_valid)
    return {"url": result.shared_link.url, "expiresAt": expires_at}


def download_document(file_id: str) -> bytes:
    client = get_client()
    stream = client.downloads.download_file(file_id)
    return stream.read() if stream else b""
