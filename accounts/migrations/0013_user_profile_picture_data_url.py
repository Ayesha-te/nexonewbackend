from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0012_fix_sardar_788_total_withdrawn"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="profile_picture_data_url",
            field=models.TextField(blank=True, default=""),
        ),
    ]
