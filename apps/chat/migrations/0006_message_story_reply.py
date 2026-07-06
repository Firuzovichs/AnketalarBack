import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stories', '0003_story_is_deleted'),
        ('chat', '0005_message_disappearing_photo_system'),
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
                    ('story_reply', 'Storyga javob'),
                ],
                default='text',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='message',
            name='story',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='chat_replies', to='stories.story',
            ),
        ),
    ]
