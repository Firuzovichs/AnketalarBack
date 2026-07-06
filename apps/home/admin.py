from django.contrib import admin
from django.utils.html import format_html
from .models import Banner, News, StaticPage


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display  = ['title', 'order', 'is_active', 'preview_image', 'created_at']
    list_editable = ['order', 'is_active']
    list_filter   = ['is_active']
    search_fields = ['title', 'description']
    ordering      = ['order']

    def preview_image(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="height:50px;border-radius:6px;object-fit:cover;" />',
                obj.image.url
            )
        return '—'
    preview_image.short_description = 'Rasm'


@admin.register(StaticPage)
class StaticPageAdmin(admin.ModelAdmin):
    """
    Biz haqimizda / Foydalanish shartlari / Maxfiylik siyosati — faqat tahrirlash,
    hech qachon o'chirish mumkin emas (ilova bu sahifalarga slug bo'yicha tayanadi).
    """
    list_display   = ['title', 'slug', 'updated_at']
    readonly_fields = ['updated_at']
    search_fields   = ['title', 'content']

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        # Faqat 3 ta belgilangan slug (about/terms/privacy) seed migratsiyada yaratiladi.
        return False


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display  = ['title', 'is_active', 'preview_image', 'published_at']
    list_editable = ['is_active']
    list_filter   = ['is_active']
    search_fields = ['title', 'description', 'content']
    readonly_fields = ['published_at', 'preview_image']

    def preview_image(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="height:80px;border-radius:8px;object-fit:cover;" />',
                obj.image.url
            )
        return '—'
    preview_image.short_description = 'Rasm'
