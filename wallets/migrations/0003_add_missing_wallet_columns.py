from django.db import migrations


def get_existing_columns(schema_editor, table_name):
    with schema_editor.connection.cursor() as cursor:
        return {
            column.name
            for column in schema_editor.connection.introspection.get_table_description(
                cursor,
                table_name,
            )
        }


def add_missing_wallet_columns(apps, schema_editor):
    Wallet = apps.get_model("wallets", "Wallet")
    table_name = Wallet._meta.db_table
    existing_columns = get_existing_columns(schema_editor, table_name)

    for field_name in ("income_pkr", "hold_pkr"):
        if field_name in existing_columns:
            continue
        schema_editor.add_field(Wallet, Wallet._meta.get_field(field_name))


def remove_wallet_columns(apps, schema_editor):
    Wallet = apps.get_model("wallets", "Wallet")
    table_name = Wallet._meta.db_table
    existing_columns = get_existing_columns(schema_editor, table_name)

    for field_name in ("hold_pkr", "income_pkr"):
        if field_name not in existing_columns:
            continue
        schema_editor.remove_field(Wallet, Wallet._meta.get_field(field_name))


class Migration(migrations.Migration):

    dependencies = [
        ("wallets", "0002_sync_legacy_wallet_columns"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(add_missing_wallet_columns, remove_wallet_columns),
            ],
            state_operations=[],
        ),
    ]
