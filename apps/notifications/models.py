from django.db import models
from django.conf import settings


class Notification(models.Model):
    TYPES = [
        ('new_like',       'Yangi like'),
        ('like_accepted',  'Like qabul qilindi'),
        ('new_message',    'Yangi xabar'),
        ('new_story',      'Yangi story'),
        ('story_reaction', 'Story reaksiya'),
        ('system',         'Tizim xabari'),
    ]

    user              = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=TYPES)
    title             = models.CharField(max_length=200)
    body              = models.TextField()
    data              = models.JSONField(default=dict)
    is_read           = models.BooleanField(default=False)
    created_at        = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.notification_type}] {self.user}: {self.title}"
