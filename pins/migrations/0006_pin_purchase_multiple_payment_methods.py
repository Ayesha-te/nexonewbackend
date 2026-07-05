from django.db import migrations, models


def default_pin_payment_methods():
    return [
        {
            "paymentMethod": "Easypaisa",
            "accountTitle": "Sardar Laeiq Ahmed",
            "accountNumber": "03448252109",
            "instructions": "Send payment to this Easypaisa account and submit your transaction ID or proof screenshot for admin approval.",
            "qrCodeUrl": None,
        }
    ]


def seed_payment_methods(apps, schema_editor):
    PinPurchaseSettings = apps.get_model("pins", "PinPurchaseSettings")
    for settings in PinPurchaseSettings.objects.all():
        if settings.payment_methods:
            continue
        qr_url = settings.qr_code.url if settings.qr_code else None
        settings.payment_methods = [
            {
                "paymentMethod": settings.payment_method,
                "accountTitle": settings.account_title,
                "accountNumber": settings.account_number,
                "instructions": settings.instructions,
                "qrCodeUrl": qr_url,
            }
        ]
        settings.save(update_fields=["payment_methods"])


class Migration(migrations.Migration):

    dependencies = [
        ("pins", "0005_pin_purchase_settings_and_screenshot"),
    ]

    operations = [
        migrations.AddField(
            model_name="pinpurchasesettings",
            name="payment_methods",
            field=models.JSONField(blank=True, default=default_pin_payment_methods),
        ),
        migrations.RunPython(seed_payment_methods, migrations.RunPython.noop),
    ]
