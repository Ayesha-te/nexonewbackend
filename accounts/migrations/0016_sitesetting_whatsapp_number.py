from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0015_restore_user_profile_picture_data_url"),
    ]

    operations = [
        migrations.AddField(
            model_name="sitesetting",
            name="whatsapp_number",
            field=models.CharField(blank=True, default="923448252109", max_length=20),
        ),
    ]
