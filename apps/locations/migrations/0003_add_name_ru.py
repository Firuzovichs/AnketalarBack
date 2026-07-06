from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('locations', '0002_seed_uzbekistan'),
    ]

    operations = [
        migrations.AddField(
            model_name='country',
            name='name_ru',
            field=models.CharField(blank=True, max_length=100, verbose_name='Ruscha nomi'),
        ),
        migrations.AddField(
            model_name='region',
            name='name_ru',
            field=models.CharField(blank=True, max_length=100, verbose_name='Ruscha nomi'),
        ),
        migrations.AddField(
            model_name='district',
            name='name_ru',
            field=models.CharField(blank=True, max_length=100, verbose_name='Ruscha nomi'),
        ),
    ]
