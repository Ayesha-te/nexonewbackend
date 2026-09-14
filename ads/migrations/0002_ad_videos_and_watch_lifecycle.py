import django.utils.timezone
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("ads", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="AdVideo",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(blank=True, default="", max_length=128)),
                ("video", models.FileField(upload_to="ads-videos/")),
                ("duration_seconds", models.PositiveIntegerField()),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.AddField(
            model_name="adwatch",
            name="video",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="watches",
                to="ads.advideo",
            ),
        ),
        migrations.AddField(
            model_name="adwatch",
            name="status",
            field=models.CharField(
                choices=[("started", "Started"), ("completed", "Completed")],
                default="completed",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="adwatch",
            name="started_at",
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name="adwatch",
            name="completed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="adwatch",
            name="reward_pkr",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
