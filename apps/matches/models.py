from django.db import models
from django.conf import settings


class Like(models.Model):
    STATUS_PENDING  = 'pending'
    STATUS_ACCEPTED = 'accepted'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES  = [
        (STATUS_PENDING,  'Kutilmoqda'),
        (STATUS_ACCEPTED, 'Qabul qilindi'),
        (STATUS_REJECTED, 'Rad etildi'),
    ]
    LIKE_TYPES = [('like', 'Like'), ('super_like', 'Super Like')]

    from_user  = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_likes')
    to_user    = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_likes')
    like_type  = models.CharField(max_length=10, choices=LIKE_TYPES, default='like')
    status     = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)
    # "Habar bilan like" — Like tab'dagi 3-tugma (X / Like / Habar bilan Like)
    # orqali ixtiyoriy ravishda yozilgan matn. Bo'sh bo'lishi mumkin (oddiy
    # like'larda). Match yuzaga kelganda (yoki keyinroq qarama-qarshi tomon
    # ham like bossa) shu matn yangi chat xonasiga BIRINCHI xabar sifatida
    # ko'chiriladi — qarang apps/matches/views.py. MUHIM: bu maydon faqat
    # YOZILADI, hech qachon o'chirilmaydi/tozalanmaydi.
    message    = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['from_user', 'to_user']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.from_user} → {self.to_user} [{self.status}]"


class Match(models.Model):
    """Ikki tomon ham like tashlagan va qabul qilgan."""
    user1      = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='matches_as_user1')
    user2      = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='matches_as_user2')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user1', 'user2']
        ordering = ['-created_at']

    def __str__(self):
        return f"Match: {self.user1} ↔ {self.user2}"

    def get_other_user(self, user):
        return self.user2 if self.user1 == user else self.user1
