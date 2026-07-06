from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class Story(models.Model):
    MEDIA_TYPES = [('image', 'Rasm'), ('video', 'Video')]

    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='stories')
    media      = models.FileField(upload_to='stories/%Y/%m/')
    media_type = models.CharField(max_length=5, choices=MEDIA_TYPES, default='image')
    caption    = models.CharField(max_length=300, blank=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Stories'

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=settings.STORY_EXPIRE_HOURS)
        super().save(*args, **kwargs)

    @property
    def is_active(self):
        return not self.is_deleted and timezone.now() < self.expires_at

    @property
    def views_count(self):
        return self.views.count()

    @property
    def reactions_count(self):
        return self.reactions.count()

    def __str__(self):
        return f"Story by {self.user} at {self.created_at:%Y-%m-%d %H:%M}"


class StoryView(models.Model):
    story     = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='views')
    viewer    = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='viewed_stories')
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['story', 'viewer']
        ordering = ['-viewed_at']


class StoryReaction(models.Model):
    story      = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='reactions')
    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    sticker    = models.CharField(max_length=50)   # emoji yoki sticker nomi
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['story', 'user']
        ordering = ['-created_at']
