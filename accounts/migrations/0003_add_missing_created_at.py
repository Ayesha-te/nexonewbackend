from django.db import migrations


def add_created_at_if_missing(apps, schema_editor):
    connection = schema_editor.connection
    introspection = connection.introspection
    tables = set(introspection.table_names())
    if "accounts_user" not in tables:
        return
    with connection.cursor() as cursor:
        columns = {
            column.name
            for column in introspection.get_table_description(cursor, "accounts_user")
        }
    if "created_at" not in columns:
        schema_editor.execute(
            'ALTER TABLE "accounts_user" ADD COLUMN "created_at" timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL'
        )


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_sync_legacy_schema"),
    ]

    operations = [
        migrations.RunPython(add_created_at_if_missing, migrations.RunPython.noop),
    ]
