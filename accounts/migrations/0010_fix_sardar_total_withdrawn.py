from django.db import migrations


def fix_total_withdrawn(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    User.objects.filter(
        email__iexact="sardarlaeiq786@gmail.com",
        total_withdrawn=9000,
    ).update(total_withdrawn=5400)


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0009_sitesetting_usd_rate"),
    ]

    operations = [
        migrations.RunPython(fix_total_withdrawn, migrations.RunPython.noop),
    ]
