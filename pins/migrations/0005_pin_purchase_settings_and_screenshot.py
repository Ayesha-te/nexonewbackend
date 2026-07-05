from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pins", "0004_add_missing_admin_note_column"),
    ]

    operations = [
        migrations.CreateModel(
            name="PinPurchaseSettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("purchase_enabled", models.BooleanField(default=True)),
                ("account_title", models.CharField(default="Sardar Laeiq Ahmed", max_length=128)),
                ("account_number", models.CharField(default="03448252109", max_length=64)),
                (
                    "payment_method",
                    models.CharField(
                        choices=[
                            ("JazzCash", "JazzCash"),
                            ("Easypaisa", "Easypaisa"),
                            ("Bank Account", "Bank Account"),
                        ],
                        default="Easypaisa",
                        max_length=32,
                    ),
                ),
                (
                    "instructions",
                    models.TextField(
                        default="Send payment to this Easypaisa account and submit your transaction ID or proof screenshot for admin approval."
                    ),
                ),
                ("qr_code", models.FileField(blank=True, null=True, upload_to="pin-payment-qr/")),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.AddField(
            model_name="pinrequest",
            name="payment_screenshot",
            field=models.FileField(blank=True, null=True, upload_to="pin-payment-screenshots/"),
        ),
        migrations.AlterField(
            model_name="pinrequest",
            name="account_number",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
    ]
