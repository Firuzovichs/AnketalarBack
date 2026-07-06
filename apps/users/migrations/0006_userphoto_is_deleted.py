from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_alter_goal_name_ru_alter_interest_name_ru'),
    ]

    operations = [
        migrations.AddField(
            model_name='userphoto',
            name='is_deleted',
            field=models.BooleanField(default=False),
        ),
    ]
