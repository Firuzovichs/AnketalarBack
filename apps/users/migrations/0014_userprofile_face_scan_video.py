from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0013_userprofile_social_links'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='face_scan_video',
            field=models.FileField(blank=True, null=True, upload_to='face_scan_videos/%Y/%m/'),
        ),
    ]
