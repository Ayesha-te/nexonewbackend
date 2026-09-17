from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("withdrawals", "0004_unique_pending_auto_withdrawal_per_user"),
    ]

    operations = [
        migrations.AddField(
            model_name="withdrawal",
            name="processed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
