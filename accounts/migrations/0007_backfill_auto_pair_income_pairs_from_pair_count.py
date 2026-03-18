from django.db import migrations, models


def sync_paid_set_counts_from_binary_pairs(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    User.objects.update(auto_pair_income_pairs=models.F("pair_count"))


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0006_backfill_auto_pair_income_pairs_from_referrals"),
    ]

    operations = [
        migrations.RunPython(sync_paid_set_counts_from_binary_pairs, migrations.RunPython.noop),
    ]
