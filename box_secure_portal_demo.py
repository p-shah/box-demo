"""
Secure Client Reporting Portal — demo script structure
Box Solutions Architect interview

Flow:
  1. Authenticate via Client Credentials Grant (CCG) — no interactive login
  2. Get/create the client's folder + apply a metadata template
  3. Upload the report and attach metadata (drives Shield classification)
  4. Generate a scoped, expiring shared link for external client access
  5. Log the action for the admin console / audit story

Requires: pip install "boxsdk<10"
"""

import datetime
import os

from boxsdk import Client, OAuth2


# ---------------------------------------------------------------------------
# 1. Auth — developer token
# ---------------------------------------------------------------------------

def get_client() -> Client:
    """
    Developer-token auth uses the Box user who generated the token, so it
    does not require an enterprise ID. Developer tokens are short-lived and
    intended for development and demos, not production integrations.
    """
    developer_token = os.environ.get("BOX_DEVELOPER_TOKEN")
    if not developer_token:
        raise RuntimeError("Set BOX_DEVELOPER_TOKEN before running the demo.")

    auth = OAuth2(client_id=None, client_secret=None, access_token=developer_token)
    return Client(auth)


# ---------------------------------------------------------------------------
# 2. Per-client folder + metadata template
# ---------------------------------------------------------------------------

METADATA_TEMPLATE_KEY = "clientReportInfo"  # created ahead of time in the Box admin console
METADATA_SCOPE = "enterprise"


def get_or_create_client_folder(client: Client, parent_folder_id: str, client_name: str):
    """
    Look for an existing folder for this client under the parent portal
    folder; create it if it doesn't exist yet.
    """
    parent = client.folder(parent_folder_id)
    for item in parent.get_items():
        if item.type == "folder" and item.name == client_name:
            return item
    return parent.create_subfolder(client_name)


def apply_metadata(client: Client, file_id: str, report_type: str, quarter: str, sensitivity: str):
    """
    Attaching structured metadata is what lets Shield apply a classification
    automatically — this call is the trigger for the governance story later
    in the demo.
    """
    metadata = {
        "reportType": report_type,     # e.g. "Quarterly Statement", "Tax Document"
        "quarter": quarter,             # e.g. "Q3-2026"
        "sensitivity": sensitivity,     # e.g. "Client Confidential"
        "generatedOn": datetime.date.today().isoformat(),
    }
    file_instance = client.file(file_id)
    return file_instance.metadata(scope=METADATA_SCOPE, template=METADATA_TEMPLATE_KEY).create(metadata)


# ---------------------------------------------------------------------------
# 3. Upload the report
# ---------------------------------------------------------------------------

def upload_report(client: Client, folder_id: str, local_path: str, file_name: str):
    folder = client.folder(folder_id)
    uploaded = folder.upload(local_path, file_name=file_name)
    return uploaded


# ---------------------------------------------------------------------------
# 4. Scoped, expiring shared link
# ---------------------------------------------------------------------------

def create_client_link(client: Client, file_id: str, days_valid: int = 14):
    """
    View-only, password-optional, auto-expiring — this is the piece the
    client actually interacts with. Shield policy (configured separately
    in the admin console) is what blocks download for Confidential items
    even over a valid link.
    """
    file_instance = client.file(file_id)
    expires_at = (
        datetime.datetime.utcnow() + datetime.timedelta(days=days_valid)
    ).isoformat() + "Z"

    shared_link = file_instance.get_shared_link(
        access="open",
        unshared_at=expires_at,
        allow_download=False,
    )
    return shared_link


# ---------------------------------------------------------------------------
# 5. Audit / admin console hook
# ---------------------------------------------------------------------------

def log_action(client_name: str, file_name: str, action: str):
    """
    Placeholder for whatever you show as the 'admin console' moment —
    could be a print statement for the live demo, or a real call to
    Box's Events API (client.events()) to pull actual audit log entries.
    """
    print(f"[{datetime.datetime.utcnow().isoformat()}Z] {action}: {file_name} for {client_name}")


# ---------------------------------------------------------------------------
# Demo run
# ---------------------------------------------------------------------------

def run_demo():
    client = get_client()

    portal_root_folder_id = "418113709484"
    client_name = "Acme Wealth Client"

    client_folder = get_or_create_client_folder(client, portal_root_folder_id, client_name)
    log_action(client_name, client_folder.name, "Folder ready")

    uploaded_file = upload_report(
        client,
        client_folder.id,
        local_path="./sample_reports/q3_statement.pdf",
        file_name="Q3_2026_Statement.pdf",
    )
    log_action(client_name, uploaded_file.name, "Uploaded")

    apply_metadata(
        client,
        uploaded_file.id,
        report_type="Quarterly Statement",
        quarter="Q3-2026",
        sensitivity="Client Confidential",
    )
    log_action(client_name, uploaded_file.name, "Metadata applied (Shield classification triggered)")

    link = create_client_link(client, uploaded_file.id, days_valid=14)
    log_action(client_name, uploaded_file.name, f"Shared link created: {link}")

    print("\nDemo complete. Client link (view-only, expires in 14 days):")
    print(link)


if __name__ == "__main__":
    run_demo()
