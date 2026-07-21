from rest_framework import serializers
from .models import ChatRoom, Message, MessageRead
from .utils import room_lock_state, room_blocked_other, room_muted_by, get_clear_timestamp
from apps.users.serializers import UserSerializer
from apps.stories.models import Story


class StoryRefSerializer(serializers.ModelSerializer):
    """`message_type='story_reply'` xabarlarda qaysi storyga javob
    yozilganini ko'rsatish uchun yengil (nested) serializer — `ReplyMessageSerializer`
    bilan bir xil uslubda. Story o'zi (yoki uning egasi) keyinchalik
    o'chirilgan (soft-delete) bo'lsa ham, bu yerda `story` maydoni shunchaki
    `None` bo'lib qoladi (FK `SET_NULL`) — xabarning o'zi hech qachon yo'qolmaydi."""

    class Meta:
        model = Story
        fields = ['id', 'media', 'media_type', 'caption']


class ReplyMessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'sender', 'message_type', 'content', 'media', 'duration', 'created_at']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # O'chib ketadigan rasmning haqiqiy fayli javob (reply) ko'rinishida
        # HECH QACHON ko'rsatilmasin — aks holda ko'rmagan kishi reply chip
        # orqali "yon eshikdan" rasmni ko'rib olishi mumkin bo'lardi.
        if instance.message_type == Message.MSG_DISAPPEARING_PHOTO:
            data['media'] = None
        return data


class MessageSerializer(serializers.ModelSerializer):
    sender        = UserSerializer(read_only=True)
    reply_to      = ReplyMessageSerializer(read_only=True)
    story         = StoryRefSerializer(read_only=True)
    is_read       = serializers.SerializerMethodField()
    seen_by_other = serializers.SerializerMethodField()
    # MUHIM: model maydoni DecimalField bo'lgani uchun, agar bu yerda aniq
    # ko'rsatilmasa, ModelSerializer uni JSON'da STRING qilib chiqaradi
    # (masalan "41.311081", raqam emas). iOS tomonda ChatMessage.latitude/
    # longitude `Double?` sifatida deshifrlanadi — JSONDecoder esa string'ni
    # Double'ga avtomatik aylantirmaydi, shu sababli butun xabarlar ro'yxati
    # (yoki suhbatlar ro'yxatidagi last_message) decode bo'lmay, "chat
    # ko'rinmay qolish" xatosiga olib kelardi (faqat ichida lokatsiya xabari
    # bor suhbatlarda). Shu sababli bu yerda aniq FloatField bilan haqiqiy
    # JSON raqam sifatida chiqaramiz.
    latitude      = serializers.FloatField(required=False, allow_null=True)
    longitude     = serializers.FloatField(required=False, allow_null=True)
    disappear_expired = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            'id', 'room', 'sender', 'message_type',
            'content', 'media', 'duration', 'latitude', 'longitude', 'reply_to', 'story',
            'disappear_seconds', 'viewed_at', 'disappear_expired',
            'is_read', 'seen_by_other', 'is_deleted', 'is_edited', 'created_at',
        ]
        read_only_fields = ['id', 'sender', 'is_deleted', 'is_edited', 'created_at', 'viewed_at']

    def get_is_read(self, obj):
        request = self.context.get('request')
        if not request:
            return False
        return obj.reads.filter(user=request.user).exclude(user=obj.sender).exists()

    def get_seen_by_other(self, obj):
        """Telegram-uslubidagi 'ko'rildi' (✓✓) belgisi uchun — jo'natuvchidan
        BOSHQA hech bo'lmaganda bitta kishi shu xabarni o'qiganmi, buni
        ko'rsatadi (kim so'rayotganiga bog'liq emas — sender ham, recipient
        ham bir xil natijani ko'radi)."""
        return obj.reads.exclude(user=obj.sender).exists()

    def get_disappear_expired(self, obj):
        return obj.disappear_expired

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Muddati o'tgan o'chib ketadigan rasm — fayl bazada/diskda qoladi
        # (hech qachon o'chirilmaydi), LEKIN endi hech kimga (jo'natuvchiga
        # ham) qaytarib ko'rsatilmaydi — faqat "muddati tugadi" holati.
        if instance.message_type == Message.MSG_DISAPPEARING_PHOTO and instance.disappear_expired:
            data['media'] = None
        return data


class SendMessageSerializer(serializers.Serializer):
    # MUHIM: 'system' bu yerda YO'Q — tizim xabarlari (masalan skrinshot
    # ogohlantirishi) faqat serverning o'zi (ScreenshotAlertView) tomonidan
    # to'g'ridan-to'g'ri Message.objects.create() orqali yaratiladi, oddiy
    # foydalanuvchi shu endpoint orqali soxta "tizim xabari" yubora olmasin.
    message_type = serializers.ChoiceField(
        choices=['text', 'image', 'video', 'video_note', 'voice', 'location', 'disappearing_photo'],
        default='text',
    )
    content      = serializers.CharField(required=False, allow_blank=True)
    media        = serializers.FileField(required=False)
    # Faqat voice/video uchun — qurilmada o'lchangan haqiqiy davomiylik (soniya).
    # Ixtiyoriy: eski klient versiyalari yubormasligi mumkin, shu sababli required=False.
    duration     = serializers.FloatField(required=False, allow_null=True)
    latitude     = serializers.FloatField(required=False)
    longitude    = serializers.FloatField(required=False)
    reply_to_id  = serializers.IntegerField(required=False)
    # Faqat disappearing_photo uchun — 3 / 5 / 10 soniya.
    disappear_seconds = serializers.ChoiceField(choices=[3, 5, 10], required=False)

    def validate(self, attrs):
        msg_type = attrs.get('message_type')
        if msg_type == 'text' and not attrs.get('content'):
            raise serializers.ValidationError({'content': 'Matn xabari uchun content kiritilishi shart.'})
        if msg_type in ['image', 'video', 'video_note', 'voice'] and not attrs.get('media'):
            raise serializers.ValidationError({'media': 'Media fayl yuborilishi shart.'})
        if msg_type == 'location' and (attrs.get('latitude') is None or attrs.get('longitude') is None):
            raise serializers.ValidationError({'latitude': 'Lokatsiya uchun latitude/longitude kiritilishi shart.'})
        if msg_type == 'disappearing_photo':
            if not attrs.get('media'):
                raise serializers.ValidationError({'media': 'Rasm fayl yuborilishi shart.'})
            if not attrs.get('disappear_seconds'):
                raise serializers.ValidationError({'disappear_seconds': "Ko'rinish davomiyligi (3/5/10) tanlanishi shart."})
        return attrs


class ChatRoomSerializer(serializers.ModelSerializer):
    other_user   = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    is_locked    = serializers.SerializerMethodField()
    expires_at   = serializers.SerializerMethodField()
    is_blocked   = serializers.SerializerMethodField()
    is_muted     = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = [
            'id', 'room_type', 'other_user', 'last_message', 'unread_count',
            'is_locked', 'expires_at', 'is_blocked', 'is_muted', 'created_at',
        ]

    def get_other_user(self, obj):
        request = self.context.get('request')
        if obj.room_type == 'admin':
            return None
        other = obj.participants.exclude(id=request.user.id).first()
        return UserSerializer(other, context=self.context).data if other else None

    def get_last_message(self, obj):
        request = self.context.get('request')
        msg = obj.last_message()
        if not msg:
            return None
        # "Chatni tozalash" qilingan bo'lsa, shu vaqtdan oldingi oxirgi xabar
        # ro'yxat ko'rinishida (preview) ham ko'rsatilmasin — bazada xabar
        # o'zgarmaydi, faqat shu foydalanuvchiga ko'rsatish filtrlanadi.
        if request:
            cleared_at = get_clear_timestamp(obj, request.user)
            if cleared_at and msg.created_at <= cleared_at:
                return None
        return MessageSerializer(msg, context=self.context).data

    def get_unread_count(self, obj):
        request = self.context.get('request')
        if not request:
            return 0
        qs = obj.messages.exclude(
            reads__user=request.user
        ).exclude(sender=request.user).filter(is_deleted=False)
        cleared_at = get_clear_timestamp(obj, request.user)
        if cleared_at:
            qs = qs.filter(created_at__gt=cleared_at)
        return qs.count()

    def get_is_locked(self, obj):
        request = self.context.get('request')
        if not request:
            return False
        locked, _ = room_lock_state(obj, request.user)
        return locked

    def get_expires_at(self, obj):
        request = self.context.get('request')
        if not request:
            return None
        _, expires_at = room_lock_state(obj, request.user)
        return expires_at

    def get_is_blocked(self, obj):
        request = self.context.get('request')
        if not request:
            return False
        return room_blocked_other(obj, request.user)

    def get_is_muted(self, obj):
        request = self.context.get('request')
        if not request:
            return False
        return room_muted_by(obj, request.user)
