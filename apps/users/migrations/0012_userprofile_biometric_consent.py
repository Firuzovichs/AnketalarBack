from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0011_terms_acceptance'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='biometric_consent_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='biometric_consent_version',
            field=models.CharField(blank=True, max_length=20),
        ),
    ]
