from django.db.models import Case, When, Value, IntegerField, Max
from django.db.models.functions import Coalesce
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics, status
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import ChatRoom, Message, MessageRead, ChatClear
from .serializers import ChatRoomSerializer, MessageSerializer, SendMessageSerializer
from .utils import (
    room_lock_state, room_blocked_other, room_muted_by, get_clear_timestamp,
    ensure_admin_room,
)
from apps.notifications.tasks import send_notification_task

CHAT_LOCKED_DETAIL = "Chat muddati tugagan. Obunani yangilang."
CHAT_BLOCKED_DETAIL = "Bu foydalanuvchi bilan suhbat bloklangan."


class ChatRoomListView(generics.ListAPIView):
    serializer_class = ChatRoomSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Har bir foydalanuvchida doim "Yordam" (admin) xonasi bo'lishi kerak —
        # ro'yxat so'ralganda yo'q bo'lsa, shu yerda yaratib qo'yamiz.
        ensure_admin_room(self.request.user)

        # Admin xonasi har doim ro'yxat boshida turadi (pin). Qolganlari esa
        # ENG SO'NGGI YOZGAN kishi tepada turishi uchun — xona yaratilgan
        # vaqti (`created_at`) emas, balki ICHIDAGI ENG SO'NGGI XABAR vaqti
        # bo'yicha tartiblanadi (avval `-created_at` ishlatilgan, shu sababli
        # kim yozsa ham xona joyidan qimirlamasdi — faqat YANGI xonalar tepaga
        # chiqardi). Hali birorta ham xabar yo'q (yangi match) xonalar uchun
        # `created_at`ga tushib qolamiz (Coalesce).
        return self.request.user.chat_rooms.all().prefetch_related(
            'participants', 'messages'
        ).annotate(
            _pin=Case(
                When(room_type='admin', then=Value(0)),
                default=Value(1), output_field=IntegerField(),
            ),
            _last_activity=Coalesce(Max('messages__created_at'), 'created_at'),
        ).order_by('_pin', '-_last_activity')


class ChatRoomDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        room = get_object_or_404(ChatRoom, pk=pk, participants=request.user)
        return Response(ChatRoomSerializer(room, context={'request': request}).data)


class AdminRoomView(APIView):
    """
    GET /api/chat/rooms/admin/
    Joriy foydalanuvchining "Yordam" xonasini qaytaradi (kerak bo'lsa
    yaratadi) — Profil/Sozlamalardagi "Yordam" tugmasi to'g'ridan-to'g'ri
    shu yerga o'tishi uchun.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        room = ensure_admin_room(request.user)
        return Response(ChatRoomSerializer(room, context={'request': request}).data)


class MessageListView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    # Standart global pagination (page_size=20) bilan suhbatda 20 tadan ko'p
    # xabar bo'lganda eng so'nggi (va aynan hozir yuborilgan!) xabarlar 1-sahifada
    # chiqmay qolardi — chatda "xabar yo'qolib qoladi" degan xato shundan edi.
    # Shu sababli bu yerda DRF'ning standart pagination'i o'chirilgan — lekin
    # PAGE_SIZE asosida QO'LDA, cursor (`?before=<id>`) bilan sahifalanadi
    # (pastga qarang) — suhbat juda uzun bo'lsa ham, ekran ochilganda FAQAT
    # oxirgi PAGE_SIZE xabar yuklanadi (tezlik uchun), eskirog'i kerak bo'lganda
    # (yuqoriga scroll) alohida so'rov bilan olinadi.
    pagination_class = None
    PAGE_SIZE = 40

    def get_queryset(self):
        room_id = self.kwargs['room_id']
        room = get_object_or_404(ChatRoom, pk=room_id, participants=self.request.user)

        # Xabarlarni o'qilgan deb belgilash
        unread = room.messages.exclude(
            reads__user=self.request.user
        ).exclude(sender=self.request.user)
        for msg in unread:
            MessageRead.objects.get_or_create(message=msg, user=self.request.user)

        qs = room.messages.filter(is_deleted=False).select_related(
            'sender', 'sender__profile',
            'reply_to', 'reply_to__sender', 'reply_to__sender__profile',
        )
        # "Chatni tozalash" qilingan bo'lsa, shu vaqtdan OLDINGI xabarlar
        # FAQAT shu foydalanuvchiga ko'rsatilmaydi — bazadagi qatorlar
        # (suhbatdosh tomonida ham) hech qachon o'zgarmaydi/o'chmaydi.
        cleared_at = get_clear_timestamp(room, self.request.user)
        if cleared_at:
            qs = qs.filter(created_at__gt=cleared_at)
        return qs

    def list(self, request, *args, **kwargs):
        # MUHIM: ikkita alohida 403 holati bor — "muddati tugagan" (eski,
        # obunaga bog'liq) va "bloklangan" (yangi). Javob shakli bir xil
        # ({'detail': ...}) qoladi, faqat 'blocked'/'locked' bayrog'i bilan
        # mijoz qaysi holatda ekanini ajrata oladi.
        room_id = self.kwargs['room_id']
        room = get_object_or_404(ChatRoom, pk=room_id, participants=request.user)

        if room_blocked_other(room, request.user):
            return Response({'detail': CHAT_BLOCKED_DETAIL, 'blocked': True, 'code': 'chat_blocked'}, status=403)

        locked, _ = room_lock_state(room, request.user)
        if locked:
            return Response({'detail': CHAT_LOCKED_DETAIL, 'locked': True, 'code': 'chat_locked'}, status=403)

        # `get_queryset()` shu yerda BIR MARTA chaqiriladi — ichida "o'qildi"
        # deb belgilash yon ta'siri bor, shu sababli sahifalashdan qat'i
        # nazar (qaysi sahifa so'ralayotganidan) HAR DOIM butun xonadagi
        # o'qilmagan xabarlar belgilanadi (bu pagination'ga bog'liq emas).
        qs = self.get_queryset().order_by('-id')

        before = request.query_params.get('before')
        if before is not None:
            try:
                qs = qs.filter(id__lt=int(before))
            except (TypeError, ValueError):
                pass

        # PAGE_SIZE + 1 ta olib, ortig'i bor-yo'qligidan `has_more`ni bilamiz
        # (qo'shimcha COUNT so'rovisiz).
        items = list(qs[: self.PAGE_SIZE + 1])
        has_more = len(items) > self.PAGE_SIZE
        items = items[: self.PAGE_SIZE]
        items.reverse()  # eskidan -> yangiga (chat ko'rinishidagi tartib)

        serializer = self.get_serializer(items, many=True)
        return Response({'results': serializer.data, 'has_more': has_more})


class MessageDetailView(generics.RetrieveAPIView):
    """Bitta xabarni ID bo'yicha to'liq (sender/media/reply_to bilan)
    qaytaradi. MUHIM: bu butun xabarlar ro'yxatini qaytadan yuklashning
    o'rnini bosadi — masalan suhbatdoshdan WebSocket orqali "yangi xabar"
    haqida xabar kelganda, klient endi BUTUN tarixni qayta so'ramaydi,
    faqat shu BITTA yangi xabarni shu endpoint orqali olib, mahalliy
    ro'yxat oxiriga qo'shadi (suhbat qancha uzun bo'lishidan qat'i nazar,
    har bir yangi xabar bir xil tezlikda keladi)."""
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Message.objects.filter(
            room__participants=self.request.user,
        ).select_related('sender', 'sender__profile', 'reply_to', 'reply_to__sender', 'reply_to__sender__profile', 'room')


class SendMessageView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, room_id):
        room = get_object_or_404(ChatRoom, pk=room_id, participants=request.user)

        if room_blocked_other(room, request.user):
            return Response({'detail': CHAT_BLOCKED_DETAIL, 'blocked': True, 'code': 'chat_blocked'}, status=403)

        locked, _ = room_lock_state(room, request.user)
        if locked:
            return Response({'detail': CHAT_LOCKED_DETAIL, 'locked': True, 'code': 'chat_locked'}, status=403)

        # Media xabar limit tekshirish
        ser = SendMessageSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        msg_type = data.get('message_type', 'text')
        sub  = getattr(request.user, 'subscription', None)
        plan = sub.plan if sub and sub.is_active else None

        if msg_type == 'voice' and not (plan and plan.can_send_voice):
            return Response({'detail': 'Ovozli xabar Premium/VIP uchun.', 'code': 'voice_premium_only'}, status=403)
        if msg_type in ('video', 'video_note') and not (plan and plan.can_send_video_msg):
            return Response({'detail': 'Video xabar Premium/VIP uchun.', 'code': 'video_premium_only'}, status=403)

        reply_to = None
        if data.get('reply_to_id'):
            try:
                reply_to = Message.objects.get(pk=data['reply_to_id'], room=room)
            except Message.DoesNotExist:
                pass

        msg = Message.objects.create(
            room=room,
            sender=request.user,
            message_type=msg_type,
            content=data.get('content', ''),
            media=data.get('media'),
            duration=data.get('duration'),
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            reply_to=reply_to,
            disappear_seconds=data.get('disappear_seconds'),
        )

        # O'qildi deb belgilash (jo'natuvchi uchun)
        MessageRead.objects.get_or_create(message=msg, user=request.user)

        # Bildirishnoma (media turiga mos qisqa yorliq bilan, agar matn bo'lmasa)
        MEDIA_NOTIF_LABELS = {
            'image': '📷 Rasm', 'video': '🎥 Video',
            'voice': '🎤 Ovozli xabar', 'location': '📍 Joylashuv',
            'disappearing_photo': '⏳ O\'chib ketadigan rasm',
        }
        other_users = room.participants.exclude(id=request.user.id)
        for other in other_users:
            # Bildirishnoma o'chirilgan bo'lsa — "hech narsa bo'lmasin": shu
            # foydalanuvchi uchun `send_notification_task` umuman chaqirilmaydi
            # (DB Notification qatori ham yaratilmaydi, FCM ham yuborilmaydi).
            # Xabarning o'zi (WebSocket orqali) bunga bog'liq emas — har doim
            # oddiy tarzda yetib boradi.
            if room_muted_by(room, other):
                continue
            send_notification_task.delay(
                user_id=other.id, notif_type='new_message',
                title=f'{request.user.profile.first_name}',
                body=data.get('content') or MEDIA_NOTIF_LABELS.get(msg_type, '📎 Media xabar'),
                data={'room_id': room.id, 'message_id': msg.id},
            )

        return Response(MessageSerializer(msg, context={'request': request}).data,
                        status=status.HTTP_201_CREATED)


class DeleteMessageView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        msg = get_object_or_404(Message, pk=pk, sender=request.user)
        msg.is_deleted = True
        msg.content = ''
        msg.save()
        return Response({'detail': 'Xabar o\'chirildi.'})


class EditMessageView(APIView):
    """
    PATCH /api/chat/messages/<pk>/edit/  {"content": "..."}
    Faqat YUBORGAN (sender) shu xabarni keyinroq tahrirlay oladi — FAQAT
    `message_type='text'` bo'lganda va hali o'chirilmagan bo'lsa (boshqa
    foydalanuvchining xabarini tahrirlab bo'lmaydi — "teskari xabarni
    faqat nusxa olish mumkin" talabi shu yerda ham, ham klient tomonida
    ta'minlanadi). MUHIM: bu Message qatorini bazadan HECH QACHON
    o'chirmaydi yoki yangisi bilan almashtirmaydi — faqat shu qatordagi
    `content` yangilanadi va `is_edited=True` qilib belgilanadi (suhbatda
    "tahrirlangan" yorlig'ini ko'rsatish uchun).
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        msg = get_object_or_404(
            Message, pk=pk, sender=request.user,
            message_type=Message.MSG_TEXT, is_deleted=False,
        )
        content = (request.data.get('content') or '').strip()
        if not content:
            return Response({'detail': "Matn bo'sh bo'lishi mumkin emas.", 'code': 'empty_message'}, status=400)
        msg.content = content
        msg.is_edited = True
        msg.save(update_fields=['content', 'is_edited'])
        return Response(MessageSerializer(msg, context={'request': request}).data)


class MarkPhotoViewedView(APIView):
    """
    POST /api/chat/messages/<pk>/view/
    O'chib ketadigan rasm birinchi marta ochilganda chaqiriladi —
    `viewed_at`ni belgilaydi, shu paytdan boshlab `disappear_seconds` hisobi
    ishga tushadi. Faqat JO'NATUVCHIDAN BOSHQA ishtirokchi chaqirganda
    ta'sir qiladi (jo'natuvchining o'zi ochib qo'yib hisoblagichni ishga
    tushirib qo'ymasligi uchun) va faqat BIR MARTA (qayta chaqirilsa
    o'zgarmaydi — vaqt qayta boshlanib ketmaydi).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        msg = get_object_or_404(
            Message, pk=pk, message_type=Message.MSG_DISAPPEARING_PHOTO,
            room__participants=request.user,
        )
        if msg.sender_id != request.user.id and not msg.viewed_at:
            msg.viewed_at = timezone.now()
            msg.save(update_fields=['viewed_at'])
        return Response(MessageSerializer(msg, context={'request': request}).data)


class ScreenshotAlertView(APIView):
    """
    POST /api/chat/rooms/<room_id>/screenshot-alert/
    iOS `UIApplication.userDidTakeScreenshotNotification`ni ushlab, shu
    yerga xabar beradi — biz buni 'system' turidagi YANGI Message qatori
    sifatida yaratamiz, shu bilan mavjud post_save broadcast signali orqali
    (apps/chat/signals.py) ikkinchi tomonga real vaqtda yetib boradi,
    alohida WebSocket o'zgartirish talab qilinmaydi.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, room_id):
        room = get_object_or_404(ChatRoom, pk=room_id, participants=request.user)

        msg = Message.objects.create(
            room=room, sender=request.user, message_type=Message.MSG_SYSTEM,
            content='screenshot_taken',
        )

        other_users = room.participants.exclude(id=request.user.id)
        for other in other_users:
            if room_muted_by(room, other):
                continue
            send_notification_task.delay(
                user_id=other.id, notif_type='system',
                title='Skrinshot olindi',
                body=f'{request.user.profile.first_name} suhbatdan skrinshot oldi.',
                data={'room_id': room.id, 'message_id': msg.id},
            )

        return Response(MessageSerializer(msg, context={'request': request}).data,
                        status=status.HTTP_201_CREATED)


class ToggleMuteView(APIView):
    """
    POST /api/chat/rooms/<pk>/mute/
    Shu xona uchun bildirishnomani yoqib/o'chirib qo'yadi (toggle).
    MUHIM: bu FAQAT `muted_by` M2M ro'yxatiga shu foydalanuvchini
    qo'shadi/olib tashlaydi — hech qanday Message yoki boshqa qator
    bazadan o'chmaydi, faqat push/in-app bildirishnoma yuborilishi shu
    foydalanuvchi uchun ushlanib qolinadi.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        room = get_object_or_404(ChatRoom, pk=pk, participants=request.user)

        if room_muted_by(room, request.user):
            room.muted_by.remove(request.user)
            muted = False
        else:
            room.muted_by.add(request.user)
            muted = True

        return Response({'is_muted': muted})


class ClearChatView(APIView):
    """
    POST /api/chat/rooms/<pk>/clear/
    "Chatni tozalash" — FAQAT shu foydalanuvchi uchun, hozirgi vaqtdan
    OLDINGI xabarlarni ko'rsatishni to'xtatadi. MUHIM (loyihaning qattiq
    qoidasi): bu hech qachon `Message` qatorlarini bazadan o'chirmaydi yoki
    o'zgartirmaydi — suhbatdosh tomonida xabarlar to'liq saqlanib qoladi va
    odatdagidek ko'rinishda davom etadi. Faqat shu foydalanuvchining
    `ChatClear.cleared_at` belgisi yangilanadi (yangi xabar kelsa, u yana
    ko'rinadi).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        room = get_object_or_404(ChatRoom, pk=pk, participants=request.user)
        ChatClear.objects.update_or_create(room=room, user=request.user)
        return Response({'detail': 'Suhbat tozalandi.'})


class SearchMessagesView(generics.ListAPIView):
    """
    GET /api/chat/rooms/<room_id>/messages/search/?q=...
    Shu xona ichida matn bo'yicha qidiradi. `MessageListView` bilan bir xil
    bloklash/qulflash tekshiruvlariga bo'ysunadi va xuddi shunday "Chatni
    tozalash" chegarasidan oldingi xabarlarni chiqarmaydi — lekin xabarlarni
    o'qilgan deb belgilamaydi (oddiy ro'yxatdan ataylab ajratilgan, faqat
    qidirish uchun yengil/yon ta'sirsiz endpoint).
    """
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        room_id = self.kwargs['room_id']
        room = get_object_or_404(ChatRoom, pk=room_id, participants=self.request.user)

        query = self.request.query_params.get('q', '').strip()
        if not query:
            return Message.objects.none()

        qs = room.messages.filter(
            is_deleted=False, content__icontains=query,
        ).select_related('sender', 'reply_to')

        cleared_at = get_clear_timestamp(room, self.request.user)
        if cleared_at:
            qs = qs.filter(created_at__gt=cleared_at)
        return qs

    def list(self, request, *args, **kwargs):
        room_id = self.kwargs['room_id']
        room = get_object_or_404(ChatRoom, pk=room_id, participants=request.user)

        if room_blocked_other(room, request.user):
            return Response({'detail': CHAT_BLOCKED_DETAIL, 'blocked': True, 'code': 'chat_blocked'}, status=403)

        locked, _ = room_lock_state(room, request.user)
        if locked:
            return Response({'detail': CHAT_LOCKED_DETAIL, 'locked': True, 'code': 'chat_locked'}, status=403)

        return super().list(request, *args, **kwargs)
