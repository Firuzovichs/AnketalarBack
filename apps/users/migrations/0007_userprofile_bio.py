from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_userphoto_is_deleted'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='bio',
            field=models.TextField(blank=True, max_length=300),
        ),
    ]
