from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0004_message_duration'),
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
                    ('disappearing_photo', "O'chib ketadigan rasm"),
                    ('system', 'Tizim xabari'),
                ],
                default='text',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='message',
            name='disappear_seconds',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='message',
            name='viewed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='message',
            name='is_expired',
            field=models.BooleanField(default=False),
        ),
    ]
