from django.db import models
from django.conf import settings


class Plan(models.Model):
    PLAN_TYPES = [('free', 'Oddiy'), ('premium', 'Premium'), ('vip', 'VIP')]

    plan_type = models.CharField(max_length=10, choices=PLAN_TYPES, unique=True)
    name = models.CharField(max_length=50)
    price_monthly = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Limits
    likes_per_day        = models.IntegerField(default=20)     # -1 = cheksiz
    super_likes_per_day  = models.IntegerField(default=0)
    can_see_who_liked    = models.BooleanField(default=False)
    can_use_radius_filter = models.BooleanField(default=False)
    can_send_voice       = models.BooleanField(default=False)
    can_send_video_msg   = models.BooleanField(default=False)
    can_boost_profile    = models.BooleanField(default=False)
    can_see_story_analytics = models.BooleanField(default=False)
    stories_per_day      = models.IntegerField(default=1)
    ad_free              = models.BooleanField(default=False)
    # Chat xonasi necha kun ochiq turadi (shu muddatdan keyin "Chat muddati
    # tugagan" holatiga o'tadi — backend/apps/chat/utils.py:room_lock_state).
    chat_duration_days   = models.PositiveIntegerField(default=3)

    # Apple App Store Connect'dagi shu tarifga mos auto-renewable subscription
    # mahsulot identifikatori (masalan "com.shoxijaxon.anketalarr.premium.monthly").
    # MUHIM: Connectda mahsulot hali yaratilmagan bo'lsa bo'sh qoldirish mumkin —
    # iOS ilova bo'sh bo'lgan tarifni xarid ro'yxatida ko'rsatmaydi. Mahsulot
    # keyinroq Connectda yaratilganda FAQAT shu maydonni shu yerda (admin
    # panelda) to'ldirish kifoya — kodga tegish shart emas.
    apple_product_id     = models.CharField(max_length=120, blank=True, default='')

    class Meta:
        ordering = ['price_monthly']

    def __str__(self):
        return self.name

    @classmethod
    def get_defaults(cls):
        """Boshlang'ich ma'lumotlarni yaratish."""
        defaults = [
            {
                'plan_type': 'free', 'name': 'Oddiy', 'price_monthly': 0,
                'likes_per_day': 20, 'super_likes_per_day': 0,
                'can_see_who_liked': False, 'can_use_radius_filter': False,
                'can_send_voice': False, 'can_send_video_msg': False,
                'can_boost_profile': False, 'can_see_story_analytics': False,
                'stories_per_day': 1, 'ad_free': False, 'chat_duration_days': 3,
            },
            {
                'plan_type': 'premium', 'name': 'Premium', 'price_monthly': 49900,
                'likes_per_day': 100, 'super_likes_per_day': 3,
                'can_see_who_liked': True, 'can_use_radius_filter': True,
                'can_send_voice': True, 'can_send_video_msg': True,
                'can_boost_profile': False, 'can_see_story_analytics': True,
                'stories_per_day': 1, 'ad_free': False, 'chat_duration_days': 7,
            },
            {
                'plan_type': 'vip', 'name': 'VIP', 'price_monthly': 99900,
                'likes_per_day': -1, 'super_likes_per_day': 10,
                'can_see_who_liked': True, 'can_use_radius_filter': True,
                'can_send_voice': True, 'can_send_video_msg': True,
                'can_boost_profile': True, 'can_see_story_analytics': True,
                'stories_per_day': 3, 'ad_free': True, 'chat_duration_days': 30,
            },
        ]
        for d in defaults:
            cls.objects.get_or_create(plan_type=d['plan_type'], defaults=d)


class UserSubscription(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscription'
    )
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)
    started_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    # Eng so'nggi tasdiqlangan Apple xaridining "original transaction id"si.
    # Apple App Store Server Notifications (yangilanish/bekor qilish/muddati
    # tugashi) kelganda aynan shu foydalanuvchini topish uchun ishlatiladi —
    # Apple bu xabarlarni har doim shu ID orqali yuboradi (alohida tranzaksiya
    # ID'lari har bir to'lovda o'zgaradi, lekin original_transaction_id butun
    # obuna umri davomida bir xil qoladi).
    apple_original_transaction_id = models.CharField(
        max_length=64, blank=True, default='', db_index=True
    )

    @property
    def is_active(self):
        from django.utils import timezone
        if self.expires_at is None:
            return True  # free plan
        return timezone.now() < self.expires_at

    def __str__(self):
        return f"{self.user} — {self.plan.name}"


class ApplePurchase(models.Model):
    """Apple App Store IAP tasdiqlash/bildirishnoma loglari.

    MUHIM (loyihaning umumiy qoidasi): bu yozuvlar APPEND-ONLY audit jurnali —
    hech qachon o'zgartirilmaydi yoki o'chirilmaydi (admin panelda ham "Delete"
    o'chirib qo'yilgan, qarang apps/subscriptions/admin.py). Har bir tekshirish
    urinishi (ilovadan kelgan xarid yoki Apple serverining bildirishnomasi)
    o'zining YANGI qatorini yaratadi — shunday qilib to'lovlar tarixi to'liq va
    o'zgarmas saqlanadi.
    """

    SOURCE_CHOICES = [
        ('device_verify', 'Ilovadan (xarid tasdiqlash)'),
        ('server_notification', 'Apple serveridan (bildirishnoma)'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='apple_purchases',
    )
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    notification_type = models.CharField(max_length=40, blank=True, default='')
    product_id = models.CharField(max_length=120, blank=True, default='')
    transaction_id = models.CharField(max_length=64, blank=True, default='')
    original_transaction_id = models.CharField(max_length=64, blank=True, default='', db_index=True)
    environment = models.CharField(max_length=20, blank=True, default='')
    expires_at = models.DateTimeField(null=True, blank=True)
    is_valid = models.BooleanField(default=True)
    error_message = models.CharField(max_length=255, blank=True, default='')
    raw_payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_source_display()} — {self.product_id or '?'} ({self.created_at:%Y-%m-%d %H:%M})"
