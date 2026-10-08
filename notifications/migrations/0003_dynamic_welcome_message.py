from django.db import migrations

NEW_WELCOME_MESSAGE = (
    "Your account has been successfully activated. Your {welcome_duration_days}-Day "
    "Welcome Ads Bonus is now available. You can watch up to {daily_limit} {ad_word} per day."
)

OLD_WELCOME_MESSAGE = (
    "Your account has been successfully activated. Your 3-Day Welcome Ads "
    "Bonus is now available. You can watch up to 3 Ads per day."
)


def apply_dynamic_message(apps, schema_editor):
    NotificationTypeConfig = apps.get_model("notifications", "NotificationTypeConfig")
    # Only overwrite if it's still the original hard-coded wording - if an admin has already
    # customized this template, leave their edit alone.
    NotificationTypeConfig.objects.filter(
        notif_type="welcome", message_template=OLD_WELCOME_MESSAGE
    ).update(message_template=NEW_WELCOME_MESSAGE)


def revert_dynamic_message(apps, schema_editor):
    NotificationTypeConfig = apps.get_model("notifications", "NotificationTypeConfig")
    NotificationTypeConfig.objects.filter(
        notif_type="welcome", message_template=NEW_WELCOME_MESSAGE
    ).update(message_template=OLD_WELCOME_MESSAGE)


class Migration(migrations.Migration):

    dependencies = [
        ("notifications", "0002_seed_notification_types"),
    ]

    operations = [
        migrations.RunPython(apply_dynamic_message, reverse_code=revert_dynamic_message),
    ]
