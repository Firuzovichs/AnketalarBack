from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from datetime import timedelta


class UserManager(BaseUserManager):
    def create_user(self, password=None, **extra_fields):
        if not extra_fields.get('email') and not extra_fields.get('phone'):
            raise ValueError('Email yoki telefon raqam kiritilishi shart.')
        user = self.model(**extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email=email, password=password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, null=True, blank=True)
    phone = models.CharField(max_length=20, unique=True, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    objects = UserManager()

    class Meta:
        verbose_name = 'Foydalanuvchi'
        verbose_name_plural = 'Foydalanuvchilar'

    def __str__(self):
        return self.email or self.phone or f'User #{self.pk}'

    @property
    def is_online(self):
        if not self.last_seen:
            return False
        return (timezone.now() - self.last_seen).seconds < 300  # 5 daqiqa


class OTPVerification(models.Model):
    identifier = models.CharField(max_length=100)   # email yoki phone
    otp = models.CharField(max_length=6)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ['-created_at']

    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at


class Interest(models.Model):
    name    = models.CharField(max_length=100)           # English
    name_uz = models.CharField(max_length=100)           # O'zbekcha
    name_ru = models.CharField(max_length=100, blank=True)  # Русский
    icon    = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.name_uz


class Goal(models.Model):
    name    = models.CharField(max_length=100)           # English
    name_uz = models.CharField(max_length=100)           # O'zbekcha
    name_ru = models.CharField(max_length=100, blank=True)  # Русский
    icon    = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.name_uz


class UserProfile(models.Model):
    GENDER_CHOICES = [('M', 'Erkak'), ('F', 'Ayol')]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    patronymic = models.CharField(max_length=100, blank=True)
    birth_date = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    bio = models.TextField(max_length=300, blank=True)
    height = models.PositiveSmallIntegerField(null=True, blank=True)   # sm
    weight = models.PositiveSmallIntegerField(null=True, blank=True)   # kg
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    district = models.ForeignKey(
        'locations.District', on_delete=models.SET_NULL, null=True, blank=True
    )
    interests = models.ManyToManyField(Interest, blank=True)
    goals = models.ManyToManyField(Goal, blank=True)
    # Social networks
    social_tiktok    = models.CharField(max_length=50, blank=True)
    social_instagram = models.CharField(max_length=50, blank=True)
    social_telegram  = models.CharField(max_length=50, blank=True)
    # Face scan
    face_scan = models.ImageField(upload_to='face_scans/%Y/%m/', null=True, blank=True)
    is_face_verified = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_complete(self):
        required = [self.first_name, self.last_name, self.birth_date, self.gender]
        return all(required) and self.is_face_verified

    @property
    def age(self):
        from utils.helpers import calculate_age
        return calculate_age(self.birth_date)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class UserPhoto(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='user_photos/%Y/%m/')
    is_main = models.BooleanField(default=False)
    order = models.PositiveSmallIntegerField(default=0)
    # MUHIM: rasmlar hech qachon bazadan butunlay o'chirilmasin — foydalanuvchi
    # "o'chirsa" ham faqat shu flag True bo'ladi (soft delete), Story modelidagi
    # is_deleted bilan bir xil konvensiya.
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_main', 'order']

    def save(self, *args, **kwargs):
        # Faqat bitta asosiy rasm bo'lsin
        if self.is_main:
            UserPhoto.objects.filter(
                user=self.user, is_main=True, is_deleted=False
            ).exclude(pk=self.pk).update(is_main=False)
        super().save(*args, **kwargs)


class Block(models.Model):
    """Foydalanuvchi boshqa birovni bloklashi. MUHIM: blokdan chiqarilganda
    qator hech qachon o'chirilmaydi (bazadan butunlay o'chirish taqiqlangan
    konvensiya) — faqat `is_active=False` qilib belgilanadi, qayta
    bloklanganda esa xuddi shu qator qayta `is_active=True` qilinadi."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocks_made')
    blocked_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocked_by')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [['user', 'blocked_user']]
        verbose_name = 'Bloklash'
        verbose_name_plural = 'Bloklashlar'

    def __str__(self):
        return f'{self.user} → {self.blocked_user} ({"faol" if self.is_active else "bekor qilingan"})'

    @staticmethod
    def is_blocked_between(user_a, user_b):
        """Ikki foydalanuvchi orasida (ikki tomonlama) faol bloklash bor-yo'qligini
        tekshiradi — kim kimni bloklagani farqi yo'q, ikkisi ham chatlasholmasligi kerak."""
        if not user_a or not user_b:
            return False
        return Block.objects.filter(
            models.Q(user=user_a, blocked_user=user_b) | models.Q(user=user_b, blocked_user=user_a),
            is_active=True,
        ).exists()

    @staticmethod
    def excluded_user_ids_for(user):
        """`user` bilan bog'liq (u bloklagan YOKI uni bloklagan) barcha foydalanuvchi
        ID'lari — qidiruv/swipe/xarita kabi joylarda ko'rsatish ro'yxatidan
        chiqarib tashlash uchun."""
        blocked = Block.objects.filter(user=user, is_active=True).values_list('blocked_user_id', flat=True)
        blocked_by = Block.objects.filter(blocked_user=user, is_active=True).values_list('user_id', flat=True)
        return set(blocked) | set(blocked_by)


class Report(models.Model):
    """Foydalanuvchi boshqa birovni adminga shikoyat qilishi — hozircha
    bloklash amali bilan birga avtomatik yaratiladi (alohida shikoyat
    endpointi yo'q), Django admin panelida ko'rib chiqish uchun."""
    REASON_CHOICES = [
        ('spam', 'Spam'),
        ('harassment', "Ta'qib/xafa qilish"),
        ('fake_profile', 'Soxta profil'),
        ('inappropriate', "Nomaqul kontent"),
        ('other', 'Boshqa'),
    ]
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_made')
    reported_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_received')
    reason = models.CharField(max_length=20, choices=REASON_CHOICES, default='other')
    description = models.TextField(blank=True)
    is_reviewed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Shikoyat'
        verbose_name_plural = 'Shikoyatlar'

    def __str__(self):
        return f'{self.reporter} → {self.reported_user} ({self.get_reason_display()})'


class AccountDeletionRequest(models.Model):
    """Foydalanuvchi hisobini o'chirish so'rovi. MUHIM: tasdiqlansa ham hisob
    yoki uning ma'lumotlari bazadan hech qachon o'chirilmaydi — faqat
    `user.is_active=False` qilinadi (LoginView shu maydonni allaqachon
    tekshiradi, shuning uchun tasdiqlangan foydalanuvchi boshqa kira olmaydi)."""
    STATUS_CHOICES = [
        ('pending',  'Kutilmoqda'),
        ('approved', 'Tasdiqlangan'),
        ('rejected', 'Rad etilgan'),
    ]
    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='deletion_requests')
    reason      = models.TextField(blank=True, verbose_name='Sabab')
    status      = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending', verbose_name='Holat')
    created_at  = models.DateTimeField(auto_now_add=True, verbose_name="So'ralgan vaqti")
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name="Ko'rib chiqilgan vaqti")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Hisobni o'chirish so'rovi"
        verbose_name_plural = "Hisobni o'chirish so'rovlari"

    def __str__(self):
        return f'{self.user} ({self.get_status_display()})'

    def approve(self):
        self.status = 'approved'
        self.reviewed_at = timezone.now()
        self.save(update_fields=['status', 'reviewed_at'])
        # Hisobni o'chirmaymiz — faqat faolsizlantiramiz, shunda LoginView
        # "Hisob bloklangan." javobini qaytaradi va u boshqa kira olmaydi.
        self.user.is_active = False
        self.user.save(update_fields=['is_active'])

    def reject(self):
        self.status = 'rejected'
        self.reviewed_at = timezone.now()
        self.save(update_fields=['status', 'reviewed_at'])
