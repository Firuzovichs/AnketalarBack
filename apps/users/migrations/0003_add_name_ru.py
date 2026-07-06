from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_seed_interests_goals'),
    ]

    operations = [
        migrations.AddField(
            model_name='interest',
            name='name_ru',
            field=models.CharField(blank=True, max_length=100, verbose_name='Ruscha nomi'),
        ),
        migrations.AddField(
            model_name='goal',
            name='name_ru',
            field=models.CharField(blank=True, max_length=100, verbose_name='Ruscha nomi'),
        ),
    ]
