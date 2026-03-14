from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pins", "0002_pin_source_request_pinrequest_processed_at"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AddField(
                    model_name="pinrequest",
                    name="admin_note",
                    field=models.TextField(blank=True, default=""),
                ),
            ],
        ),
    ]
