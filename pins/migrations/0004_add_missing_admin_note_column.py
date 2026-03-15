from django.db import migrations


def add_admin_note_column(apps, schema_editor):
    PinRequest = apps.get_model("pins", "PinRequest")
    table_name = PinRequest._meta.db_table
    existing_columns = {
        column.name for column in schema_editor.connection.introspection.get_table_description(
            schema_editor.connection.cursor(),
            table_name,
        )
    }

    if "admin_note" in existing_columns:
        return

    schema_editor.add_field(PinRequest, PinRequest._meta.get_field("admin_note"))


def remove_admin_note_column(apps, schema_editor):
    PinRequest = apps.get_model("pins", "PinRequest")
    table_name = PinRequest._meta.db_table
    existing_columns = {
        column.name for column in schema_editor.connection.introspection.get_table_description(
            schema_editor.connection.cursor(),
            table_name,
        )
    }

    if "admin_note" not in existing_columns:
        return

    schema_editor.remove_field(PinRequest, PinRequest._meta.get_field("admin_note"))


class Migration(migrations.Migration):

    dependencies = [
        ("pins", "0003_sync_admin_note_state"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(add_admin_note_column, remove_admin_note_column),
            ],
            state_operations=[],
        ),
    ]
