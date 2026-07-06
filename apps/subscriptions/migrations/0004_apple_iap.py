from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('subscriptions', '0003_plan_chat_duration_days'),
    ]

    operations = [
        migrations.AddField(
            model_name='plan',
            name='apple_product_id',
            field=models.CharField(blank=True, default='', max_length=120),
        ),
        migrations.AddField(
            model_name='usersubscription',
            name='apple_original_transaction_id',
            field=models.CharField(blank=True, db_index=True, default='', max_length=64),
        ),
        migrations.CreateModel(
            name='ApplePurchase',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source', models.CharField(choices=[('device_verify', 'Ilovadan (xarid tasdiqlash)'), ('server_notification', 'Apple serveridan (bildirishnoma)')], max_length=20)),
                ('notification_type', models.CharField(blank=True, default='', max_length=40)),
                ('product_id', models.CharField(blank=True, default='', max_length=120)),
                ('transaction_id', models.CharField(blank=True, default='', max_length=64)),
                ('original_transaction_id', models.CharField(blank=True, db_index=True, default='', max_length=64)),
                ('environment', models.CharField(blank=True, default='', max_length=20)),
                ('expires_at', models.DateTimeField(blank=True, null=True)),
                ('is_valid', models.BooleanField(default=True)),
                ('error_message', models.CharField(blank=True, default='', max_length=255)),
                ('raw_payload', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='apple_purchases', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
