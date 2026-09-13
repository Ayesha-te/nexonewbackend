import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("accounts", "0015_restore_user_profile_picture_data_url"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="NotificationTypeConfig",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "notif_type",
                    models.CharField(
                        choices=[
                            ("welcome", "Welcome"),
                            ("ads_available", "Ads Available"),
                            ("ads_reminder", "Ads Reminder"),
                            ("pair_completed", "Pair Completed"),
                            ("ads_unlocked", "Ads Unlocked"),
                            ("ads_cycle_renewed", "Ads Cycle Renewed"),
                            ("ads_cycle_ending", "Ads Cycle Ending"),
                            ("ads_locked", "Ads Locked"),
                            ("daily_ads_completed", "Daily Ads Completed"),
                            ("admin_custom", "Admin Custom"),
                        ],
                        max_length=32,
                        unique=True,
                    ),
                ),
                ("enabled", models.BooleanField(default=True)),
                ("title_template", models.CharField(max_length=255)),
                ("message_template", models.TextField()),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="Notification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "notif_type",
                    models.CharField(
                        choices=[
                            ("welcome", "Welcome"),
                            ("ads_available", "Ads Available"),
                            ("ads_reminder", "Ads Reminder"),
                            ("pair_completed", "Pair Completed"),
                            ("ads_unlocked", "Ads Unlocked"),
                            ("ads_cycle_renewed", "Ads Cycle Renewed"),
                            ("ads_cycle_ending", "Ads Cycle Ending"),
                            ("ads_locked", "Ads Locked"),
                            ("daily_ads_completed", "Daily Ads Completed"),
                            ("admin_custom", "Admin Custom"),
                        ],
                        max_length=32,
                    ),
                ),
                ("title", models.CharField(max_length=255)),
                ("message", models.TextField()),
                ("is_read", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="notifications",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]
