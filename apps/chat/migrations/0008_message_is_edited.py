from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0007_chat_mute_clear'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='is_edited',
            field=models.BooleanField(default=False),
        ),
    ]
