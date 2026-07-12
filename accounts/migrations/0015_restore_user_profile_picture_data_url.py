from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0014_remove_user_profile_picture_data_url"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="profile_picture_data_url",
            field=models.TextField(blank=True, default=""),
        ),
    ]
