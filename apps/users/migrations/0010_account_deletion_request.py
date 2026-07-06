import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('users', '0009_alter_block_id_alter_report_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='AccountDeletionRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reason', models.TextField(blank=True, verbose_name='Sabab')),
                ('status', models.CharField(choices=[('pending', 'Kutilmoqda'), ('approved', 'Tasdiqlangan'), ('rejected', 'Rad etilgan')], default='pending', max_length=10, verbose_name='Holat')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name="So'ralgan vaqti")),
                ('reviewed_at', models.DateTimeField(blank=True, null=True, verbose_name="Ko'rib chiqilgan vaqti")),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='deletion_requests', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': "Hisobni o'chirish so'rovi",
                'verbose_name_plural': "Hisobni o'chirish so'rovlari",
                'ordering': ['-created_at'],
            },
        ),
    ]
