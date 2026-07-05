from django.db import migrations


SUPPORTED_PIN_PAYMENT_METHODS = ("JazzCash", "Easypaisa", "Bank Account")


def add_active_state(apps, schema_editor):
    PinPurchaseSettings = apps.get_model("pins", "PinPurchaseSettings")

    for settings in PinPurchaseSettings.objects.all():
        saved_methods = settings.payment_methods or []
        methods_by_name = {
            str(method.get("paymentMethod", "")).strip(): method
            for method in saved_methods
            if isinstance(method, dict)
        }

        active_method = None
        for method in saved_methods:
            if isinstance(method, dict) and method.get("active"):
                active_method = str(method.get("paymentMethod", "")).strip()
                break
        if not active_method:
            active_method = settings.payment_method or "Easypaisa"

        settings.payment_methods = [
            {
                "paymentMethod": payment_method,
                "accountTitle": methods_by_name.get(payment_method, {}).get("accountTitle", ""),
                "accountNumber": methods_by_name.get(payment_method, {}).get("accountNumber", ""),
                "instructions": methods_by_name.get(payment_method, {}).get("instructions", ""),
                "qrCodeUrl": methods_by_name.get(payment_method, {}).get("qrCodeUrl"),
                "active": payment_method == active_method,
            }
            for payment_method in SUPPORTED_PIN_PAYMENT_METHODS
        ]
        settings.purchase_enabled = any(method["active"] for method in settings.payment_methods)
        settings.save(update_fields=["payment_methods", "purchase_enabled"])


class Migration(migrations.Migration):

    dependencies = [
        ("pins", "0008_pin_purchase_available_again_time"),
    ]

    operations = [
        migrations.RunPython(add_active_state, migrations.RunPython.noop),
    ]
