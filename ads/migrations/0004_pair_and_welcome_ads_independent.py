from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ads", "0003_advideo_video_storage"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="adscycle",
            name="unique_active_ads_cycle_per_user",
        ),
        migrations.AddConstraint(
            model_name="adscycle",
            constraint=models.UniqueConstraint(
                condition=models.Q(("status", "active")),
                fields=("user", "cycle_type"),
                name="unique_active_ads_cycle_per_user_type",
            ),
        ),
    ]
