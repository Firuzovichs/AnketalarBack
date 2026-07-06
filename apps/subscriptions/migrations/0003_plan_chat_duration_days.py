from django.db import migrations, models


def backfill_chat_duration_days(apps, schema_editor):
    """Mavjud Plan qatorlari uchun to'g'ri qiymatlarni qo'yib chiqamiz —
    AddField standart qiymati (3) hammasiga tegib ketmasligi uchun."""
    Plan = apps.get_model('subscriptions', 'Plan')
    days_by_type = {'free': 3, 'premium': 7, 'vip': 30}
    for plan_type, days in days_by_type.items():
        Plan.objects.filter(plan_type=plan_type).update(chat_duration_days=days)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='plan',
            name='chat_duration_days',
            field=models.PositiveIntegerField(default=3),
        ),
        migrations.RunPython(backfill_chat_duration_days, noop),
    ]
