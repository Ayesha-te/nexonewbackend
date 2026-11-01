from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pins", "0011_pin_price_1000"),
    ]

    operations = [
        migrations.AddField(
            model_name="pinpurchasesettings",
            name="standard_price",
            field=models.PositiveIntegerField(default=1000),
        ),
        migrations.AddField(
            model_name="pinpurchasesettings",
            name="promo_enabled",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="pinpurchasesettings",
            name="promo_price",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="pinpurchasesettings",
            name="promo_start_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="pinpurchasesettings",
            name="promo_end_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
