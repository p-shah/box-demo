"""
Flask API for the Secure Client Reporting Portal demo.

Serves a custom React front end (see ../frontend) so the whole demo runs
outside the Box web app: client/document browsing, upload + classification,
Box AI summaries and structured extraction, and scoped shared links.
"""

import io

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS

import box_service
from box_sdk_gen.box.errors import BoxAPIError, BoxSDKError

load_dotenv()

app = Flask(__name__)
CORS(app)


def _error_response(exc: Exception, status: int = 502):
    message = str(exc)
    if isinstance(exc, BoxAPIError):
        message = exc.message or message
    return jsonify({"error": message}), status


@app.errorhandler(RuntimeError)
def handle_runtime_error(exc):
    return jsonify({"error": str(exc)}), 500


@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/api/clients")
def get_clients():
    try:
        return jsonify(box_service.list_clients())
    except BoxSDKError as exc:
        return _error_response(exc)


@app.get("/api/clients/<folder_id>/documents")
def get_documents(folder_id):
    try:
        return jsonify(box_service.list_documents(folder_id))
    except BoxSDKError as exc:
        return _error_response(exc)


@app.get("/api/search")
def get_search():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify([])
    try:
        return jsonify(box_service.search_documents(query))
    except BoxSDKError as exc:
        return _error_response(exc)


@app.post("/api/documents")
def post_document():
    if "file" not in request.files:
        return jsonify({"error": "Missing file upload"}), 400
    upload = request.files["file"]
    report_type = request.form.get("reportType", "Quarterly Statement")
    sensitivity = request.form.get("sensitivity", "Client Confidential")

    try:
        result = box_service.upload_document(
            # box-sdk-gen needs a real seekable stream for multipart upload;
            # Flask's FileStorage.stream (a SpooledTemporaryFile) doesn't
            # reliably expose .seekable(), so read it into BytesIO first.
            io.BytesIO(upload.read()),
            upload.filename,
            report_type,
            sensitivity,
        )
        return jsonify(result), 201
    except BoxSDKError as exc:
        return _error_response(exc)


@app.post("/api/documents/summary")
def post_summary():
    body = request.get_json(silent=True) or {}
    file_ids = body.get("fileIds") or []
    file_names = body.get("fileNames") or []
    client_name = body.get("clientName", "Client")
    if not file_ids:
        return jsonify({"error": "fileIds is required"}), 400
    try:
        return jsonify(box_service.get_ai_summary(file_ids, file_names, client_name))
    except BoxSDKError as exc:
        return _error_response(exc)


@app.post("/api/documents/highlights")
def post_highlights():
    body = request.get_json(silent=True) or {}
    file_ids = body.get("fileIds") or []
    file_names = body.get("fileNames") or []
    client_name = body.get("clientName", "Client")
    if not file_ids:
        return jsonify({"error": "fileIds is required"}), 400
    try:
        return jsonify(box_service.get_ai_highlights(file_ids, file_names, client_name))
    except BoxSDKError as exc:
        return _error_response(exc)


@app.post("/api/documents/holdings-diff")
def post_holdings_diff():
    body = request.get_json(silent=True) or {}
    file_ids = body.get("fileIds") or []
    file_names = body.get("fileNames") or []
    client_name = body.get("clientName", "Client")
    if len(file_ids) != 2 or len(file_names) != 2:
        return jsonify({"error": "holdings-diff requires exactly two documents, in [from, to] order"}), 400
    try:
        return jsonify(
            box_service.get_holdings_diff(
                file_ids[0], file_names[0], file_ids[1], file_names[1], client_name
            )
        )
    except BoxSDKError as exc:
        return _error_response(exc)


@app.post("/api/documents/<file_id>/share")
def post_share_link(file_id):
    body = request.get_json(silent=True) or {}
    file_name = body.get("fileName", "document")
    client_name = body.get("clientName", "Client")
    days_valid = int(body.get("daysValid", 14))
    try:
        return jsonify(
            box_service.create_shared_link(file_id, file_name, client_name, days_valid)
        )
    except BoxSDKError as exc:
        return _error_response(exc)


@app.get("/api/documents/<file_id>/content")
def get_document_content(file_id):
    file_name = request.args.get("fileName", "statement.pdf")
    try:
        content = box_service.download_document(file_id)
    except BoxSDKError as exc:
        return _error_response(exc)
    return send_file(
        io.BytesIO(content),
        mimetype="application/pdf",
        download_name=file_name,
        as_attachment=False,
    )


@app.get("/api/activity")
def get_activity():
    return jsonify(box_service.get_activity_log())


if __name__ == "__main__":
    app.run(debug=True, port=5001)
