from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("withdrawals", "0003_withdrawal_binary_plan_fields"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="withdrawal",
            constraint=models.UniqueConstraint(
                condition=models.Q(("status", "pending"), ("auto_generated", True)),
                fields=("user",),
                name="unique_pending_auto_withdrawal_per_user",
            ),
        ),
    ]
