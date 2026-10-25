from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pins", "0010_pin_price_600"),
    ]

    operations = [
        migrations.AlterField(
            model_name="pin",
            name="amount",
            field=models.PositiveIntegerField(default=1000),
        ),
    ]
