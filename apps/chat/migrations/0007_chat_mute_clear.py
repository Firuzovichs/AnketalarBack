# Generated manually for chat mute + clear-chat feature.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('chat', '0006_message_story_reply'),
    ]

    operations = [
        migrations.AddField(
            model_name='chatroom',
            name='muted_by',
            field=models.ManyToManyField(blank=True, related_name='muted_chat_rooms', to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='ChatClear',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cleared_at', models.DateTimeField(auto_now=True)),
                ('room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='clears', to='chat.chatroom')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chat_clears', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('room', 'user')},
            },
        ),
    ]
