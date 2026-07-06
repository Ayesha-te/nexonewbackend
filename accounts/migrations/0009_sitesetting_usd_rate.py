from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0008_user_bank_name_activation_bank_account"),
    ]

    operations = [
        migrations.CreateModel(
            name="SiteSetting",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("usd_rate_pkr", models.DecimalField(decimal_places=2, default=280, max_digits=10)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
