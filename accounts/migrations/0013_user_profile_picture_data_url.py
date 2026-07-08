import base64
import mimetypes

from django.db import migrations, models


def backfill_profile_picture_data_urls(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    for user in User.objects.exclude(profile_picture="").filter(profile_picture_data_url=""):
        try:
            with user.profile_picture.open("rb") as image_file:
                encoded = base64.b64encode(image_file.read()).decode("ascii")
        except Exception:
            continue

        content_type = mimetypes.guess_type(user.profile_picture.name)[0] or "image/jpeg"
        user.profile_picture_data_url = f"data:{content_type};base64,{encoded}"
        user.save(update_fields=["profile_picture_data_url"])


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
        migrations.RunPython(backfill_profile_picture_data_urls, migrations.RunPython.noop),
    ]
