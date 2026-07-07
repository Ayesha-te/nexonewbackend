from django.db import migrations


def fix_total_withdrawn(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    User.objects.filter(email__iexact="sardarlaeiq788@gmail.com").update(total_withdrawn=2200)


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0011_fix_additional_total_withdrawn"),
    ]

    operations = [
        migrations.RunPython(fix_total_withdrawn, migrations.RunPython.noop),
    ]
