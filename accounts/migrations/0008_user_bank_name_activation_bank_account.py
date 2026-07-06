from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0007_backfill_auto_pair_income_pairs_from_pair_count"),
    ]

    operations = [
        migrations.AddField(
            model_name="pinactivationrequest",
            name="bank_name",
            field=models.CharField(blank=True, default="", max_length=128),
        ),
        migrations.AddField(
            model_name="user",
            name="bank_name",
            field=models.CharField(blank=True, default="", max_length=128),
        ),
        migrations.AlterField(
            model_name="pinactivationrequest",
            name="payment_method",
            field=models.CharField(
                choices=[
                    ("easypaisa", "EasyPaisa"),
                    ("jazzcash", "JazzCash"),
                    ("bank_account", "Bank Account"),
                ],
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="payment_method",
            field=models.CharField(
                choices=[
                    ("easypaisa", "EasyPaisa"),
                    ("jazzcash", "JazzCash"),
                    ("bank_account", "Bank Account"),
                ],
                default="easypaisa",
                max_length=20,
            ),
        ),
    ]
