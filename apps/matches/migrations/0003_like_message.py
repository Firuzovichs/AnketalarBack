# "Habar bilan like" — Like modeliga ixtiyoriy matn maydoni qo'shadi.
# Eski qatorlar uchun standart bo'sh satr ('') — hech narsa o'chirilmaydi.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('matches', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='like',
            name='message',
            field=models.TextField(blank=True, default=''),
        ),
    ]
