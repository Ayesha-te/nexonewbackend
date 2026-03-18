from django.db import migrations, models


def backfill_auto_pair_income_pairs(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    User.objects.filter(auto_pair_income_pairs=0).update(
        auto_pair_income_pairs=models.F("pair_count")
    )


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0004_create_missing_accounts_tables"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="auto_pair_income_pairs",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.RunPython(backfill_auto_pair_income_pairs, migrations.RunPython.noop),
    ]
