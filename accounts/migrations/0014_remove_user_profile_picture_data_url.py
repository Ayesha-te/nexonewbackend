from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0013_user_profile_picture_data_url"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="user",
            name="profile_picture_data_url",
        ),
    ]
