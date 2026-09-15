from django.db import migrations, models

import ads.models


class Migration(migrations.Migration):

    dependencies = [
        ("ads", "0002_ad_videos_and_watch_lifecycle"),
    ]

    operations = [
        migrations.AlterField(
            model_name="advideo",
            name="video",
            field=models.FileField(storage=ads.models.get_ad_video_storage, upload_to="ads-videos/"),
        ),
    ]
