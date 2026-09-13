from django.db import migrations

DEFAULT_TYPES = [
    {
        "notif_type": "welcome",
        "title_template": "🎉 Welcome to NexoCart",
        "message_template": (
            "Your account has been successfully activated. Your 3-Day Welcome Ads "
            "Bonus is now available. You can watch up to 3 Ads per day."
        ),
    },
    {
        "notif_type": "ads_available",
        "title_template": "📺 Ads Available",
        "message_template": (
            "Your daily Ads are available. Watch up to 3 Ads today and complete "
            "your daily Ads task."
        ),
    },
    {
        "notif_type": "ads_reminder",
        "title_template": "⏳ Ads Reminder",
        "message_template": (
            "You still have Ads available for today. Complete your remaining Ads "
            "before today's limit resets."
        ),
    },
    {
        "notif_type": "pair_completed",
        "title_template": "🎉 Pair Completed",
        "message_template": (
            "Congratulations! Your qualifying Binary Pair has been completed "
            "successfully."
        ),
    },
    {
        "notif_type": "ads_unlocked",
        "title_template": "🔓 Ads Unlocked",
        "message_template": (
            "Congratulations! Your new 3-Day Ads Cycle is now active. You can "
            "watch up to 3 Ads per day. Start Date: {start_date} End Date: {end_date}"
        ),
    },
    {
        "notif_type": "ads_cycle_renewed",
        "title_template": "🔄 Ads Cycle Renewed",
        "message_template": (
            "Your latest qualifying Pair has renewed your Ads Cycle. Your new "
            "3-Day Ads Cycle starts today. Start Date: {start_date} End Date: {end_date}"
        ),
    },
    {
        "notif_type": "ads_cycle_ending",
        "title_template": "⚠️ Ads Cycle Ending",
        "message_template": (
            "Your current Ads Cycle will end soon. Check your Binary progress to "
            "continue your next eligible Ads cycle."
        ),
    },
    {
        "notif_type": "ads_locked",
        "title_template": "🔒 Ads Cycle Completed",
        "message_template": (
            "Your current Ads Cycle has ended. Complete a new qualifying Binary "
            "Pair to unlock the next 3-Day Ads Cycle."
        ),
    },
    {
        "notif_type": "daily_ads_completed",
        "title_template": "✅ Daily Ads Completed",
        "message_template": (
            "Great job! You have completed today's 3 Ads. Your next Ads will be "
            "available after the daily reset."
        ),
    },
    {
        "notif_type": "admin_custom",
        "title_template": "Notification",
        "message_template": "",
    },
]


def seed_defaults(apps, schema_editor):
    NotificationTypeConfig = apps.get_model("notifications", "NotificationTypeConfig")
    for entry in DEFAULT_TYPES:
        NotificationTypeConfig.objects.get_or_create(
            notif_type=entry["notif_type"],
            defaults={
                "enabled": True,
                "title_template": entry["title_template"],
                "message_template": entry["message_template"],
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ("notifications", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_defaults, reverse_code=migrations.RunPython.noop),
    ]
