# Qo'lda yozilgan migratsiya — sandboxda haqiqiy Django muhiti (DB) yo'qligi
# sababli `makemigrations` ishga tushirilmadi, shu sababli 0001/0002 uslubiga
# mos qilib qo'lda yaratildi.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0002_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='message_type',
            field=models.CharField(
                choices=[
                    ('text', 'Matn'),
                    ('image', 'Rasm'),
                    ('video', 'Video'),
                    ('voice', 'Ovozli'),
                    ('location', 'Joylashuv'),
                ],
                default='text', max_length=10,
            ),
        ),
        migrations.AddField(
            model_name='message',
            name='latitude',
            field=models.DecimalField(decimal_places=6, max_digits=9, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='message',
            name='longitude',
            field=models.DecimalField(decimal_places=6, max_digits=9, null=True, blank=True),
        ),
    ]
