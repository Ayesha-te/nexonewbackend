from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pins", "0009_pin_payment_method_active_state"),
    ]

    operations = [
        migrations.AlterField(
            model_name="pin",
            name="amount",
            field=models.PositiveIntegerField(default=600),
        ),
    ]
