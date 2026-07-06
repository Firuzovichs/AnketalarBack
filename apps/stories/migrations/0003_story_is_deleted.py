from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stories', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='story',
            name='is_deleted',
            field=models.BooleanField(default=False),
        ),
    ]
