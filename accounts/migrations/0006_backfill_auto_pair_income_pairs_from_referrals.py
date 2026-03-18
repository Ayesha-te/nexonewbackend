from django.db import migrations


def sync_paid_set_counts(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    for user in User.objects.all().iterator():
        completed_sets = user.referrals.count() // 2
        if user.auto_pair_income_pairs != completed_sets:
            user.auto_pair_income_pairs = completed_sets
            user.save(update_fields=["auto_pair_income_pairs"])


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0005_user_auto_pair_income_pairs"),
    ]

    operations = [
        migrations.RunPython(sync_paid_set_counts, migrations.RunPython.noop),
    ]
