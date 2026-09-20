import os
from box_sdk_gen import (
    BoxClient,
    BoxDeveloperTokenAuth,
    CreateMetadataTemplateFields,
    CreateMetadataTemplateFieldsTypeField,
)

def create_portal_metadata_template():
    developer_token = os.environ.get("BOX_DEVELOPER_TOKEN")

    if not developer_token:
        raise RuntimeError("Set BOX_DEVELOPER_TOKEN in environment variables before running.")

    # Modern Auth & Client initialization
    auth = BoxDeveloperTokenAuth(token=developer_token)
    client = BoxClient(auth=auth)

    # Schema definition using typed objects with snake_case parameters
    fields = [
        CreateMetadataTemplateFields(
            type=CreateMetadataTemplateFieldsTypeField.STRING,
            key="reportType",
            display_name="Report Type"
        ),
        CreateMetadataTemplateFields(
            type=CreateMetadataTemplateFieldsTypeField.STRING,
            key="quarter",
            display_name="Quarter"
        ),
        CreateMetadataTemplateFields(
            type=CreateMetadataTemplateFieldsTypeField.STRING,
            key="sensitivity",
            display_name="Sensitivity"
        ),
        CreateMetadataTemplateFields(
            type=CreateMetadataTemplateFieldsTypeField.STRING,
            key="generatedOn",
            display_name="Generated On"
        ),
    ]

    try:
        template = client.metadata_templates.create_metadata_template(
            scope="enterprise",
            template_key="clientReportInfo",
            display_name="Client Report Info",
            fields=fields
        )
        print(f"Metadata Template successfully created: {template.display_name}")
    except Exception as e:
        print(f"Template setup note: {e}")

if __name__ == "__main__":
    create_portal_metadata_template()