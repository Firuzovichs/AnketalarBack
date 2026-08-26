from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0012_userprofile_biometric_consent'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],   # ustunlar allaqachon mavjud — DB ga teginmaymiz
            state_operations=[
                migrations.AddField(
                    model_name='userprofile',
                    name='social_tiktok',
                    field=models.CharField(blank=True, max_length=255),
                ),
                migrations.AddField(
                    model_name='userprofile',
                    name='social_instagram',
                    field=models.CharField(blank=True, max_length=255),
                ),
                migrations.AddField(
                    model_name='userprofile',
                    name='social_telegram',
                    field=models.CharField(blank=True, max_length=255),
                ),
            ],
        ),
    ]
