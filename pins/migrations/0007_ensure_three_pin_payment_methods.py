from django.db import migrations


SUPPORTED_PIN_PAYMENT_METHODS = ("JazzCash", "Easypaisa", "Bank Account")


def ensure_three_payment_methods(apps, schema_editor):
    PinPurchaseSettings = apps.get_model("pins", "PinPurchaseSettings")

    for settings in PinPurchaseSettings.objects.all():
        saved_methods = settings.payment_methods or []
        methods_by_name = {
            str(method.get("paymentMethod", "")).strip(): method
            for method in saved_methods
            if isinstance(method, dict)
        }

        if settings.payment_method and settings.payment_method not in methods_by_name:
            methods_by_name[settings.payment_method] = {
                "paymentMethod": settings.payment_method,
                "accountTitle": settings.account_title,
                "accountNumber": settings.account_number,
                "instructions": settings.instructions,
                "qrCodeUrl": settings.qr_code.url if settings.qr_code else None,
            }

        settings.payment_methods = [
            {
                "paymentMethod": payment_method,
                "accountTitle": methods_by_name.get(payment_method, {}).get("accountTitle", ""),
                "accountNumber": methods_by_name.get(payment_method, {}).get("accountNumber", ""),
                "instructions": methods_by_name.get(payment_method, {}).get("instructions", ""),
                "qrCodeUrl": methods_by_name.get(payment_method, {}).get("qrCodeUrl"),
            }
            for payment_method in SUPPORTED_PIN_PAYMENT_METHODS
        ]
        settings.save(update_fields=["payment_methods"])


class Migration(migrations.Migration):

    dependencies = [
        ("pins", "0006_pin_purchase_multiple_payment_methods"),
    ]

    operations = [
        migrations.RunPython(ensure_three_payment_methods, migrations.RunPython.noop),
    ]
