from django.db import migrations


def create_missing_accounts_tables(apps, schema_editor):
    connection = schema_editor.connection
    introspection = connection.introspection
    existing_tables = set(introspection.table_names())

    PinActivationRequest = apps.get_model("accounts", "PinActivationRequest")
    SignupLead = apps.get_model("accounts", "SignupLead")

    if "accounts_pinactivationrequest" not in existing_tables:
        schema_editor.create_model(PinActivationRequest)
    if "accounts_signuplead" not in existing_tables:
        schema_editor.create_model(SignupLead)


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_add_missing_created_at"),
    ]

    operations = [
        migrations.RunPython(create_missing_accounts_tables, migrations.RunPython.noop),
    ]
