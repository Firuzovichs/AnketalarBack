import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket endpoint: ws://host/ws/chat/<room_id>/
    Headers: Authorization: Bearer <access_token>
    """

    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group = f'chat_{self.room_id}'
        self.user = self.scope.get('user')

        if not self.user or not self.user.is_authenticated:
            await self.close(code=4001)
            return

        # Foydalanuvchi shu room'ga tegishli ekanligini tekshirish
        if not await self.is_room_participant():
            await self.close(code=4003)
            return

        # Chat muddati tugagan bo'lsa (obuna darajasiga qarab) ulanishga
        # ruxsat berilmaydi — admin (yordam) xonasi bundan mustasno.
        if await self.is_room_locked():
            await self.close(code=4004)
            return

        # Bloklangan suhbatga WebSocket orqali ham ulanib bo'lmaydi.
        if await self.is_room_blocked():
            await self.close(code=4005)
            return

        await self.channel_layer.group_add(self.room_group, self.channel_name)
        await self.accept()

        # Online statusni yangilash
        await self.update_last_seen()

        # Suhbatdagi boshqa tomonga "onlayn bo'ldim" deb JONLI (real-vaqt)
        # xabar beramiz — shu orqali ChatConversationView sarlavhasidagi
        # online/offline holat suhbat OCHIQ turgan paytda ham yangilanadi
        # (oldin bu faqat suhbat ochilgan paytdagi holatda "muzlab" qolardi).
        await self.channel_layer.group_send(self.room_group, {
            'type': 'presence_status', 'user_id': self.user.id, 'is_online': True,
        })

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group, self.channel_name)
        await self.update_last_seen()
        await self.channel_layer.group_send(self.room_group, {
            'type': 'presence_status', 'user_id': self.user.id, 'is_online': False,
        })

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        action = data.get('action')

        if action == 'send_message':
            await self.handle_send_message(data)
        elif action == 'typing':
            await self.handle_typing(data)
        elif action == 'read':
            await self.handle_read(data)

    # ── Handlers ─────────────────────────────────────────────────

    async def handle_send_message(self, data):
        msg_type = data.get('message_type', 'text')
        content  = data.get('content', '')
        reply_id = data.get('reply_to_id')

        # Broadcast endi Message modelining post_save signali orqali
        # (apps/chat/signals.py) AVTOMATIK amalga oshadi — save_message()
        # ichidagi Message.objects.create() chaqirilgan zahoti guruhga
        # yuboriladi, shu sababli bu yerda qayta group_send qilish kerak
        # emas (aks holda xabar ikki marta kelardi).
        await self.save_message(msg_type, content, reply_id)

    async def handle_typing(self, data):
        await self.channel_layer.group_send(self.room_group, {
            'type':      'typing_indicator',
            'user_id':   self.user.id,
            'is_typing': data.get('is_typing', False),
        })

    async def handle_read(self, data):
        message_id = data.get('message_id')
        if message_id:
            await self.mark_as_read(message_id)
            await self.channel_layer.group_send(self.room_group, {
                'type':       'message_read',
                'message_id': message_id,
                'user_id':    self.user.id,
            })

    # ── Group event handlers ──────────────────────────────────────

    async def chat_message(self, event):
        # Android/iOS `type` maydonini tekshiradi — `event` emas.
        # `message` nested ob'ektni to'liq yuboramiz (reply_to, sender bilan).
        await self.send(text_data=json.dumps({
            'type':    'chat_message',
            'message': event.get('message', {}),
        }))

    async def typing_indicator(self, event):
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type':      'typing',
                'user_id':   event['user_id'],
                'is_typing': event.get('is_typing', False),
            }))

    async def presence_status(self, event):
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type':      'presence',
                'user_id':   event['user_id'],
                'is_online': event['is_online'],
            }))

    async def message_read(self, event):
        await self.send(text_data=json.dumps({
            'type':       'message_read',
            'message_id': event['message_id'],
            'user_id':    event['user_id'],
        }))

    # ── DB helpers ────────────────────────────────────────────────

    @database_sync_to_async
    def is_room_participant(self):
        from .models import ChatRoom
        return ChatRoom.objects.filter(pk=self.room_id, participants=self.user).exists()

    @database_sync_to_async
    def is_room_locked(self):
        from .models import ChatRoom
        from .utils import room_lock_state
        try:
            room = ChatRoom.objects.get(pk=self.room_id)
        except ChatRoom.DoesNotExist:
            return True
        locked, _ = room_lock_state(room, self.user)
        return locked

    @database_sync_to_async
    def is_room_blocked(self):
        from .models import ChatRoom
        from .utils import room_blocked_other
        try:
            room = ChatRoom.objects.get(pk=self.room_id)
        except ChatRoom.DoesNotExist:
            return True
        return room_blocked_other(room, self.user)

    @database_sync_to_async
    def save_message(self, msg_type, content, reply_id):
        from .models import ChatRoom, Message, MessageRead
        from .utils import room_lock_state, room_blocked_other
        try:
            room = ChatRoom.objects.get(pk=self.room_id)
            locked, _ = room_lock_state(room, self.user)
            if locked:
                return None
            if room_blocked_other(room, self.user):
                return None
            reply = Message.objects.get(pk=reply_id) if reply_id else None
            msg = Message.objects.create(
                room=room, sender=self.user,
                message_type=msg_type, content=content, reply_to=reply,
            )
            MessageRead.objects.get_or_create(message=msg, user=self.user)
            return {'id': msg.id, 'created_at': msg.created_at.isoformat()}
        except Exception:
            return None

    @database_sync_to_async
    def mark_as_read(self, message_id):
        from .models import Message, MessageRead
        try:
            msg = Message.objects.get(pk=message_id, room_id=self.room_id)
            MessageRead.objects.get_or_create(message=msg, user=self.user)
        except Message.DoesNotExist:
            pass

    @database_sync_to_async
    def update_last_seen(self):
        # AnonymousUser.save() mavjud emas — authenticated tekshiruv qilamiz
        if not self.user or not getattr(self.user, 'is_authenticated', False):
            return
        self.user.last_seen = timezone.now()
        self.user.save(update_fields=['last_seen'])
