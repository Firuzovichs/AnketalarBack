from django.db import models


class Banner(models.Model):
    """Reklama bannerlari — admin paneldan qo'shiladi."""
    title       = models.CharField(max_length=200, verbose_name='Sarlavha')
    description = models.TextField(blank=True, verbose_name='Tavsif')
    image       = models.ImageField(upload_to='banners/', verbose_name='Rasm')
    link_url    = models.URLField(blank=True, verbose_name='Havola URL')
    is_active   = models.BooleanField(default=True, verbose_name='Faol')
    order       = models.PositiveSmallIntegerField(default=0, verbose_name='Tartib')
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = 'Banner'
        verbose_name_plural = 'Bannerlar'

    def __str__(self):
        return self.title


class StaticPage(models.Model):
    """
    Statik sahifalar — Biz haqimizda / Foydalanish shartlari / Maxfiylik siyosati.
    Kontent to'liq admin paneldan tahrirlanadi, ilova faqat slug bo'yicha o'qiydi.
    Hech qachon bazadan o'chirilmaydi (admin orqali ham) — faqat tahrirlanadi.
    """
    SLUG_CHOICES = [
        ('about',   'Biz haqimizda'),
        ('terms',   'Foydalanish shartlari'),
        ('privacy', 'Maxfiylik siyosati'),
    ]
    slug       = models.SlugField(max_length=30, unique=True, choices=SLUG_CHOICES, verbose_name='Slug')
    title      = models.CharField(max_length=200, verbose_name='Sarlavha')
    version    = models.CharField(max_length=20, default='1.0', verbose_name='Versiya')
    content    = models.TextField(verbose_name='Kontent')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Yangilangan vaqti')

    class Meta:
        ordering = ['slug']
        verbose_name = 'Statik sahifa'
        verbose_name_plural = 'Statik sahifalar'

    def __str__(self):
        return self.title


class News(models.Model):
    """Yangiliklar — admin paneldan qo'shiladi."""
    title        = models.CharField(max_length=255, verbose_name='Sarlavha')
    description  = models.TextField(verbose_name='Qisqa tavsif')
    content      = models.TextField(blank=True, verbose_name='To\'liq kontent')
    image        = models.ImageField(upload_to='news/', verbose_name='Rasm')
    is_active    = models.BooleanField(default=True, verbose_name='Faol')
    published_at = models.DateTimeField(auto_now_add=True, verbose_name='Nashr vaqti')

    class Meta:
        ordering = ['-published_at']
        verbose_name = 'Yangilik'
        verbose_name_plural = 'Yangiliklar'

    def __str__(self):
        return self.title
