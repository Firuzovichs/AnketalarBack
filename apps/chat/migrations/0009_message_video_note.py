from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0008_message_is_edited'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='message_type',
            field=models.CharField(
                default='text',
                max_length=20,
                choices=[
                    ('text', 'Matn'),
                    ('image', 'Rasm'),
                    ('video', 'Video'),
                    ('voice', 'Ovozli'),
                    ('location', 'Joylashuv'),
                    ('disappearing_photo', "O'chib ketadigan rasm"),
                    ('system', 'Tizim xabari'),
                    ('story_reply', 'Storyga javob'),
                    ('video_note', 'Video xabar (doira)'),
                ],
            ),
        ),
    ]
