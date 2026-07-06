from django.contrib import admin
from .models import ChatRoom, Message, MessageRead


class MessageInline(admin.TabularInline):
    """ChatRoom admin sahifasida xabarlarni ko'rish VA javob yozish uchun.
    `sender` maydoni ataylab formada ko'rsatilmaydi — yangi qator
    saqlanganda kim yozayotgani avtomatik joriy admin (request.user)
    qilib belgilanadi (ChatRoomAdmin.save_formset'ga qarang).

    can_delete = False — xabarlar bazadan HECH QACHON haqiqatan o'chmasligi
    kerak (faqat is_deleted=True bilan "yumshoq" o'chiriladi). Standart
    Django admin inline'da delete checkbox bo'lib, belgilab saqlash haqiqiy
    SQL DELETE qiladi — buni butunlay o'chirib qo'yamiz."""
    model = Message
    extra = 1
    can_delete = False
    fields = ['from_display', 'message_type', 'content', 'media', 'latitude', 'longitude', 'is_deleted', 'created_at']
    readonly_fields = ['from_display', 'created_at']
    ordering = ['created_at']

    def from_display(self, obj):
        if obj is None or obj.pk is None:
            return '— (saqlanganda: Siz)'
        return '🛟 Siz (admin)' if obj.sender.is_staff else f'👤 {obj.sender}'
    from_display.short_description = 'Kimdan'


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display  = ['id', 'room_type', 'participants_display', 'message_count', 'last_message_preview', 'created_at']
    list_filter   = ['room_type']
    search_fields = ['participants__email', 'participants__phone']
    # Standart M2M widget userlar ro'pchasi katta bo'lganda noqulay (hammasi
    # bitta ro'yxatda, qidiruv yo'q) — autocomplete esa email/telefon bo'yicha
    # qidirib, kerakli userni tezda tanlash imkonini beradi (UserAdmin'da
    # search_fields allaqachon bor, shu sababli ishlaydi).
    autocomplete_fields = ['participants']
    inlines       = [MessageInline]

    def participants_display(self, obj):
        return ', '.join(str(p) for p in obj.participants.all()) or '—'
    participants_display.short_description = 'Ishtirokchilar'

    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = 'Xabarlar soni'

    def last_message_preview(self, obj):
        msg = obj.last_message()
        if not msg:
            return '—'
        text = msg.content or f'[{msg.message_type}]'
        return text[:60]
    last_message_preview.short_description = "So'nggi xabar"

    def save_formset(self, request, form, formset, change):
        """Inline orqali qo'shilgan YANGI xabarlarning jo'natuvchisini
        joriy admin foydalanuvchisi qilib belgilaymiz (standart Django
        admin pattern: https://docs.djangoproject.com/en/stable/ref/contrib/admin/#django.contrib.admin.ModelAdmin.save_formset)."""
        instances = formset.save(commit=False)
        for instance in instances:
            if instance.pk is None:
                instance.sender = request.user
            instance.save()
        formset.save_m2m()


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display  = ['id', 'room', 'sender', 'message_type', 'short_content', 'is_deleted', 'is_edited', 'created_at']
    list_filter   = ['message_type', 'is_deleted', 'is_edited']
    search_fields = ['content', 'sender__email', 'sender__phone']
    # raw_id_fields o'rniga autocomplete — qidiruv maydoni bilan, ID'ni bilish
    # shart emas (ChatRoomAdmin/UserAdmin/MessageAdmin'da search_fields bor,
    # shu sababli har uchovi uchun ham ishlaydi).
    autocomplete_fields = ['room', 'sender', 'reply_to']
    ordering      = ['-created_at']

    def short_content(self, obj):
        return (obj.content or '')[:60]
    short_content.short_description = 'Matn'

    # Xabarlar bazadan HECH QACHON haqiqatan o'chmasligi kerak — shu sababli
    # bu yerda HAR XIL o'chirish yo'li (individual "Delete" tugmasi va
    # ro'yxatdagi "Delete selected messages" ommaviy amali) butunlay
    # o'chiriladi. Foydalanuvchi xabarni o'chirganda ham faqat is_deleted=True
    # qo'yiladi (apps/chat/views.py DeleteMessageView) — qatorning o'zi
    # bazada saqlanib qoladi.
    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(MessageRead)
