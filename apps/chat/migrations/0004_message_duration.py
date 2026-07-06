from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0003_message_location'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='duration',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
