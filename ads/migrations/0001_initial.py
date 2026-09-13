import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("accounts", "0015_restore_user_profile_picture_data_url"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AdsSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('enabled', models.BooleanField(default=True)),
                ('daily_limit', models.PositiveIntegerField(default=3)),
                ('welcome_reward_pkr', models.PositiveIntegerField(default=11)),
                ('welcome_duration_days', models.PositiveIntegerField(default=3)),
                ('pair_reward_pkr', models.PositiveIntegerField(default=5)),
                ('pair_cycle_days', models.PositiveIntegerField(default=3)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='AdsCycle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cycle_type', models.CharField(choices=[('welcome', 'Welcome'), ('pair', 'Pair')], max_length=16)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('status', models.CharField(choices=[('active', 'Active'), ('expired', 'Expired')], default='active', max_length=16)),
                ('ending_notified', models.BooleanField(default=False)),
                ('expired_notified', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ads_cycles', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='AdWatch',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('watched_date', models.DateField()),
                ('reward_pkr', models.PositiveIntegerField()),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('cycle', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='watches', to='ads.adscycle')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ad_watches', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddConstraint(
            model_name='adscycle',
            constraint=models.UniqueConstraint(condition=models.Q(('status', 'active')), fields=('user',), name='unique_active_ads_cycle_per_user'),
        ),
    ]
