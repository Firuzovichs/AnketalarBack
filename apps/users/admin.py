from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, UserProfile, UserPhoto, Interest, Goal, OTPVerification, Block, Report, AccountDeletionRequest


class UserProfileInline(admin.StackedInline):
    """User yaratilayotgan/tahrirlanayotgan sahifaning O'ZIDA ism-familiya va
    boshqa profil ma'lumotlarini to'ldirish imkonini beradi. Buning yo'qligi
    sabab edi: "Users -> Add user" orqali yaratilgan test foydalanuvchida
    UserProfile umuman yo'q bo'lib qolardi (faqat email/phone/parol so'raladi),
    va shu sabab ilova ichida (masalan chatda) uning ismi o'rniga umumiy
    "Foydalanuvchi" yozuvi chiqib qolardi — chunki ko'rsatish uchun ism manbai
    aynan shu UserProfile.first_name/last_name."""
    model = UserProfile
    extra = 1
    max_num = 1
    can_delete = False
    fields = ['first_name', 'last_name', 'patronymic', 'birth_date', 'gender', 'bio']


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display  = ['id', 'email', 'phone', 'is_active', 'is_email_verified', 'created_at']
    search_fields = ['email', 'phone']
    ordering      = ['-created_at']
    inlines       = [UserProfileInline]
    fieldsets     = (
        (None, {'fields': ('email', 'phone', 'password')}),
        ('Huquqlar', {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_email_verified', 'is_phone_verified')}),
    )
    add_fieldsets = (
        (None, {'fields': ('email', 'phone', 'password1', 'password2')}),
    )

    def get_inline_instances(self, request, obj=None):
        # Yangi user hali saqlanmagan bo'lsa (Add sahifasi birinchi marta
        # ochilganda) inline'ni yashiramiz — chunki UserProfile.user maydoni
        # OneToOne va hali mavjud bo'lmagan User'ga bog'lab bo'lmaydi. Lekin
        # "Add user" formasi (email/phone/parol) birinchi marta yuborilgach,
        # Django avval User'ni saqlaydi va o'sha SAQLANGAN obyekt bilan
        # sahifani qayta ko'rsatadi — shunda obj endi mavjud bo'ladi va
        # pastda profil maydonlari to'ldirish uchun paydo bo'ladi.
        if not obj:
            return []
        return super().get_inline_instances(request, obj)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'first_name', 'last_name', 'gender', 'birth_date', 'is_face_verified']
    fields = [
        'user', 'first_name', 'last_name', 'patronymic', 'birth_date', 'gender', 'bio',
        'height', 'weight', 'latitude', 'longitude', 'district',
        'interests', 'goals', 'is_face_verified',
    ]
    autocomplete_fields = ['user']
    filter_horizontal = ['interests', 'goals']

@admin.register(Interest)
class InterestAdmin(admin.ModelAdmin):
    list_display  = ['id', 'icon', 'name_uz', 'name_ru', 'name']
    search_fields = ['name', 'name_uz', 'name_ru']
    list_editable = ['name_uz', 'name_ru', 'icon']

@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display  = ['id', 'icon', 'name_uz', 'name_ru', 'name']
    search_fields = ['name', 'name_uz', 'name_ru']
    list_editable = ['name_uz', 'name_ru', 'icon']

@admin.register(UserPhoto)
class UserPhotoAdmin(admin.ModelAdmin):
    """Standart `admin.site.register(UserPhoto)` har bir qatorni shunchaki
    "UserPhoto object (N)" deb ko'rsatardi — rasm kimga tegishli ekanini
    bilish uchun har birini alohida ochib ko'rish kerak edi. Endi ro'yxatning
    o'zida kichik rasm (eskiz) + foydalanuvchi ismi/email/telefoni ko'rinadi,
    shu bilan birga email/ism bo'yicha qidirish va userga qarab tartiblash
    ham mumkin."""
    list_display   = ['id', 'thumbnail', 'owner_display', 'is_main', 'is_deleted', 'order', 'created_at']
    list_filter    = ['is_main', 'is_deleted']
    search_fields  = ['user__email', 'user__phone', 'user__profile__first_name', 'user__profile__last_name']
    autocomplete_fields = ['user']
    ordering       = ['user', '-is_main', 'order']
    list_select_related = ['user', 'user__profile']

    # MUHIM: rasmlar (boshqa hamma narsa kabi) bazadan hech qachon butunlay
    # o'chirilmasin — shuning uchun adminda ham "Delete" tugmasi/bulk action
    # o'chirib qo'yilgan (apps/chat/admin.py dagi xabarlar uchun ishlatilgan
    # xuddi shu konvensiya). Foydalanuvchi ilova ichidan rasm o'chirsa,
    # backend buni faqat is_deleted=True qilib belgilaydi (soft delete).
    def has_delete_permission(self, request, obj=None):
        return False

    def thumbnail(self, obj):
        if not obj.image:
            return '—'
        return format_html(
            '<img src="{}" style="width:48px;height:48px;object-fit:cover;border-radius:6px;" />',
            obj.image.url,
        )
    thumbnail.short_description = 'Rasm'

    def owner_display(self, obj):
        profile = getattr(obj.user, 'profile', None)
        full_name = f'{profile.first_name} {profile.last_name}'.strip() if profile else ''
        contact = obj.user.email or obj.user.phone or f'ID {obj.user_id}'
        return f'{full_name} ({contact})' if full_name else contact
    owner_display.short_description = 'Foydalanuvchi'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'user__profile')


admin.site.register(OTPVerification)


@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    list_display  = ['id', 'user', 'blocked_user', 'is_active', 'created_at']
    list_filter   = ['is_active']
    search_fields = ['user__email', 'user__phone', 'blocked_user__email', 'blocked_user__phone']
    autocomplete_fields = ['user', 'blocked_user']
    ordering      = ['-created_at']

    # MUHIM: bloklash yozuvi hech qachon bazadan butunlay o'chirilmasin —
    # blokdan chiqarish faqat is_active=False qilib amalga oshiriladi
    # (boshqa hamma joydagi soft-delete konvensiyasi bilan bir xil).
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AccountDeletionRequest)
class AccountDeletionRequestAdmin(admin.ModelAdmin):
    """Hisobni o'chirish so'rovlari. "Tasdiqlash" action'i hisobni bazadan
    o'CHIRMAYDI — faqat user.is_active=False qiladi (model.approve() ichida),
    shu sababli foydalanuvchi shunchaki login qila olmay qoladi."""
    list_display  = ['id', 'user', 'status', 'created_at', 'reviewed_at']
    list_filter   = ['status']
    search_fields = ['user__email', 'user__phone']
    autocomplete_fields = ['user']
    ordering      = ['-created_at']
    readonly_fields = ['created_at', 'reviewed_at']
    actions       = ['approve_requests', 'reject_requests']

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.action(description="Tanlangan so'rovlarni tasdiqlash (hisobni faolsizlantirish)")
    def approve_requests(self, request, queryset):
        count = 0
        for req in queryset.filter(status='pending'):
            req.approve()
            count += 1
        self.message_user(request, f'{count} ta so\'rov tasdiqlandi, tegishli hisoblar faolsizlantirildi.')

    @admin.action(description="Tanlangan so'rovlarni rad etish")
    def reject_requests(self, request, queryset):
        count = 0
        for req in queryset.filter(status='pending'):
            req.reject()
            count += 1
        self.message_user(request, f'{count} ta so\'rov rad etildi.')


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    """Foydalanuvchilar bloklash chog'ida yuborgan shikoyatlar — admin shu
    yerda ko'rib chiqib, kerak bo'lsa `is_reviewed` belgisini qo'yadi."""
    list_display  = ['id', 'reporter', 'reported_user', 'reason', 'is_reviewed', 'created_at']
    list_filter   = ['reason', 'is_reviewed']
    search_fields = ['reporter__email', 'reporter__phone', 'reported_user__email', 'reported_user__phone', 'description']
    autocomplete_fields = ['reporter', 'reported_user']
    ordering      = ['-created_at']
    list_editable = ['is_reviewed']

    def has_delete_permission(self, request, obj=None):
        return False
