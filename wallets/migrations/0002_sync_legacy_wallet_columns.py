from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wallets", "0001_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AddField(
                    model_name="wallet",
                    name="income_pkr",
                    field=models.IntegerField(default=0),
                ),
                migrations.AddField(
                    model_name="wallet",
                    name="hold_pkr",
                    field=models.IntegerField(default=0),
                ),
            ],
        ),
    ]
