from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("withdrawals", "0002_withdrawal_account_name_withdrawal_bank_name_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="withdrawal",
            name="admin_adjustment",
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name="withdrawal",
            name="admin_note",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="withdrawal",
            name="left_team_total",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="withdrawal",
            name="matched_pairs",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="withdrawal",
            name="right_team_total",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="withdrawal",
            name="system_added_earnings",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
