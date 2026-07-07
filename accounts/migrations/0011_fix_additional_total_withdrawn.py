from django.db import migrations


WITHDRAW_TOTAL_FIXES = [
    ("sardarlaeiq791@gmail.com", 2000, 1000),
    ("sardarlaeiq792@gmail.com", 1400, 1000),
    ("sardarlaeiq797@gmail.com", 1400, 400),
]


def fix_total_withdrawn(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    for email, wrong_total, corrected_total in WITHDRAW_TOTAL_FIXES:
        User.objects.filter(
            email__iexact=email,
            total_withdrawn=wrong_total,
        ).update(total_withdrawn=corrected_total)


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0010_fix_sardar_total_withdrawn"),
    ]

    operations = [
        migrations.RunPython(fix_total_withdrawn, migrations.RunPython.noop),
    ]
