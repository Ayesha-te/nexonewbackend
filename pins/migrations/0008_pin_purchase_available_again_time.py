from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pins", "0007_ensure_three_pin_payment_methods"),
    ]

    operations = [
        migrations.AddField(
            model_name="pinpurchasesettings",
            name="available_again_time",
            field=models.CharField(blank=True, default="", max_length=32),
        ),
    ]
