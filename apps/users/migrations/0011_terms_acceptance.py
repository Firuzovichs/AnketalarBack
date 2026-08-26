import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0003_staticpage_version_and_terms'),
        ('users', '0010_account_deletion_request'),
    ]

    operations = [
        migrations.CreateModel(
            name='TermsAcceptance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version', models.CharField(max_length=20, verbose_name='Shartlar versiyasi')),
                ('content_hash', models.CharField(max_length=64, verbose_name='Matn SHA-256 xeshi')),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True, verbose_name='IP manzil')),
                ('user_agent', models.CharField(blank=True, max_length=500, verbose_name='Qurilma maʼlumoti')),
                ('accepted_at', models.DateTimeField(auto_now_add=True, verbose_name='Rozilik vaqti')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='terms_acceptances', to=settings.AUTH_USER_MODEL, verbose_name='Foydalanuvchi')),
            ],
            options={
                'verbose_name': 'Foydalanish shartlariga rozilik',
                'verbose_name_plural': 'Foydalanish shartlariga roziliklar',
                'ordering': ['-accepted_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='termsacceptance',
            constraint=models.UniqueConstraint(fields=('user', 'version', 'content_hash'), name='unique_user_terms_acceptance'),
        ),
    ]
