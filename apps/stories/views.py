from django.db.models import Q
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics, status

from .models import Story, StoryView, StoryReaction
from .serializers import (
    StorySerializer, StoryCreateSerializer,
    StoryViewSerializer, StoryReactionSerializer, ReactToStorySerializer,
    ReplyToStorySerializer,
)
from apps.matches.models import Match, Like
from apps.notifications.tasks import send_notification_task
from apps.chat.models import Message, MessageRead
from apps.chat.serializers import MessageSerializer
from apps.chat.utils import get_or_create_match_room, room_lock_state, room_blocked_other, room_muted_by


def get_match_users(user):
    """Userning match bo'lgan foydalanuvchilar IDlari."""
    matches = Match.objects.filter(Q(user1=user) | Q(user2=user))
    ids = set()
    for m in matches:
        ids.add(m.user1_id if m.user2_id == user.id else m.user2_id)
    return ids


def get_liked_users(user):
    """Userga like bosgan foydalanuvchilar IDlari (story notification uchun)."""
    return set(Like.objects.filter(to_user=user).values_list('from_user_id', flat=True))


class StoryFeedView(generics.ListAPIView):
    """Match bo'lgan odamlarning aktiv storyalari."""
    serializer_class = StorySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        match_ids = get_match_users(self.request.user)
        return Story.objects.filter(
            user_id__in=match_ids,
            is_deleted=False,
            expires_at__gt=timezone.now(),
        ).select_related('user').prefetch_related('views', 'reactions')


class StoryCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        # Kunlik limit tekshirish
        sub = getattr(user, 'subscription', None)
        plan = sub.plan if sub and sub.is_active else None
        limit = plan.stories_per_day if plan else 1
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        count = Story.objects.filter(user=user, created_at__gte=today_start, is_deleted=False).count()
        if count >= limit:
            return Response({'detail': f'Kunlik story limit ({limit}) tugadi.', 'code': 'daily_story_limit', 'limit': limit}, status=429)

        ser = StoryCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        story = ser.save(user=user)

        # Match va like bosgan foydalanuvchilarni xabardor qilish
        recipient_ids = get_liked_users(user) | get_match_users(user)
        name = getattr(getattr(user, 'profile', None), 'first_name', None) or user.email
        actor_photo = None
        try:
            main_photo = user.photos.filter(is_main=True).first()
            if main_photo and main_photo.image:
                actor_photo = request.build_absolute_uri(main_photo.image.url)
        except Exception:
            pass
        for uid in recipient_ids:
            send_notification_task.delay(
                user_id=uid, notif_type='new_story',
                title='Yangi story!',
                body=f'{name} yangi story qo\'ydi.',
                data={'story_id': story.id, 'actor_name': name, 'actor_photo': actor_photo},
            )
        return Response(StorySerializer(story, context={'request': request}).data,
                        status=status.HTTP_201_CREATED)


class StoryDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            story = Story.objects.get(pk=pk, is_deleted=False)
        except Story.DoesNotExist:
            return Response({'detail': 'Story topilmadi.', 'code': 'story_not_found'}, status=404)

        # Ko'rish yozish
        if story.user != request.user:
            StoryView.objects.get_or_create(story=story, viewer=request.user)

        return Response(StorySerializer(story, context={'request': request}).data)

    def delete(self, request, pk):
        """Soft delete — DB dan o'chmaydi, faqat is_deleted=True."""
        try:
            story = Story.objects.get(pk=pk, user=request.user)
        except Story.DoesNotExist:
            return Response({'detail': 'Story topilmadi.', 'code': 'story_not_found'}, status=404)
        story.is_deleted = True
        story.save(update_fields=['is_deleted'])
        return Response(status=status.HTTP_204_NO_CONTENT)


class StoryViewView(APIView):
    """Story ko'rish — POST /api/stories/{pk}/view/"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            story = Story.objects.get(pk=pk, is_deleted=False)
        except Story.DoesNotExist:
            return Response({'detail': 'Story topilmadi.', 'code': 'story_not_found'}, status=404)
        if story.user != request.user:
            StoryView.objects.get_or_create(story=story, viewer=request.user)
        return Response({'status': 'ok'})


class MyStoriesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        stories = Story.objects.filter(
            user=request.user,
            is_deleted=False,
            expires_at__gt=timezone.now(),
        )
        return Response(StorySerializer(stories, many=True, context={'request': request}).data)


class StoryViewersView(generics.ListAPIView):
    """Story egasi kim ko'rganini ko'radi."""
    serializer_class = StoryViewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        try:
            story = Story.objects.get(pk=self.kwargs['pk'], user=self.request.user)
        except Story.DoesNotExist:
            return StoryView.objects.none()
        return story.views.select_related('viewer')


class StoryReactionsView(generics.ListAPIView):
    """Story egasi kimlar stiker bosganini ko'radi."""
    serializer_class = StoryReactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        try:
            story = Story.objects.get(pk=self.kwargs['pk'], user=self.request.user)
        except Story.DoesNotExist:
            return StoryReaction.objects.none()
        return story.reactions.select_related('user')


STICKER_EMOJI = {
    'heart': '❤️',
    'love':  '😍',
    'laugh': '😂',
    'fire':  '🔥',
    'wow':   '😮',
}


class ReactToStoryView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            story = Story.objects.get(pk=pk, is_deleted=False)
        except Story.DoesNotExist:
            return Response({'detail': 'Story topilmadi.', 'code': 'story_not_found'}, status=404)

        ser = ReactToStorySerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        reaction, created = StoryReaction.objects.update_or_create(
            story=story, user=request.user,
            defaults={'sticker': ser.validated_data['sticker']},
        )

        if story.user != request.user:
            # Reaksiya qo'ygan odam ko'rganlar ro'yxatiga ham qo'shiladi
            StoryView.objects.get_or_create(story=story, viewer=request.user)

            name = getattr(getattr(request.user, 'profile', None), 'first_name', None) or request.user.email
            emoji = STICKER_EMOJI.get(reaction.sticker, reaction.sticker)
            actor_photo = None
            try:
                main_photo = request.user.photos.filter(is_main=True).first()
                if main_photo and main_photo.image:
                    actor_photo = request.build_absolute_uri(main_photo.image.url)
            except Exception:
                pass
            send_notification_task.delay(
                user_id=story.user.id, notif_type='story_reaction',
                title='Story reaksiya!',
                body=f'{name} storyingizga {emoji} reaksiya berdi.',
                data={'story_id': story.id, 'actor_name': name, 'actor_photo': actor_photo},
            )
        return Response(StoryReactionSerializer(reaction, context={'request': request}).data)


class ReplyToStoryView(APIView):
    """
    POST /api/stories/<pk>/reply/  {"text": "..."}
    Story ko'rilayotganda yozilgan matnni storyning egasiga CHATDA maxsus
    "story javobi" (`story_reply`) turidagi Message sifatida yuboradi —
    Instagram'dagi "reply to story" funksiyasi. MUHIM: bu oddiy
    SendMessageSerializer orqali EMAS, balki ScreenshotAlertView'dagi kabi
    to'g'ridan-to'g'ri Message.objects.create() orqali yaratiladi — shu
    sababli mijoz o'zi soxta 'story_reply' xabar yasab yubora olmaydi
    (xuddi 'system' turi himoyalanganidek). Yaratilgan Message post_save
    signali orqali (apps/chat/signals.py) ikkinchi tomonga avtomatik
    WebSocket orqali yetib boradi — bu yerda alohida broadcast kerak emas.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            story = Story.objects.get(pk=pk, is_deleted=False)
        except Story.DoesNotExist:
            return Response({'detail': 'Story topilmadi.', 'code': 'story_not_found'}, status=404)

        if story.user_id == request.user.id:
            return Response({'detail': "O'zingizning storyingizga javob yozolmaysiz.", 'code': 'cant_reply_own_story'}, status=400)

        # Story-feedda faqat MATCH bo'lgan odamlarning storyalari ko'rinadi
        # (StoryFeedView.get_queryset) — javob yozish uchun ham xuddi shu
        # qoidani qo'llaymiz, link orqali to'g'ridan-to'g'ri pk yuborilsa ham.
        if story.user_id not in get_match_users(request.user):
            return Response({'detail': "Bu storyga javob yozish uchun ruxsat yo'q.", 'code': 'story_reply_forbidden'}, status=403)

        ser = ReplyToStorySerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        text = ser.validated_data['text']

        room = get_or_create_match_room(request.user, story.user)

        if room_blocked_other(room, request.user):
            return Response({'detail': 'Bu foydalanuvchi bilan suhbat bloklangan.', 'blocked': True, 'code': 'chat_blocked'}, status=403)
        locked, _ = room_lock_state(room, request.user)
        if locked:
            return Response({'detail': 'Chat muddati tugagan. Obunani yangilang.', 'locked': True, 'code': 'chat_locked'}, status=403)

        msg = Message.objects.create(
            room=room, sender=request.user, message_type=Message.MSG_STORY_REPLY,
            content=text, story=story,
        )
        # O'qildi deb belgilash (jo'natuvchi uchun) — SendMessageView bilan bir xil.
        MessageRead.objects.get_or_create(message=msg, user=request.user)

        name = getattr(getattr(request.user, 'profile', None), 'first_name', None) or request.user.email
        # Story egasi shu xona uchun bildirishnomani o'chirib qo'ygan bo'lsa —
        # "hech narsa bo'lmasin": chaqiriq umuman qilinmaydi (DB Notification
        # qatori ham yaratilmaydi). Xabarning o'zi yuqorida allaqachon
        # yaratilgan va WebSocket orqali odatdagidek yetib boradi.
        if not room_muted_by(room, story.user):
            send_notification_task.delay(
                user_id=story.user.id, notif_type='new_message',
                title=name,
                body=f'📖 {text}',
                data={'room_id': room.id, 'message_id': msg.id},
            )

        return Response(MessageSerializer(msg, context={'request': request}).data,
                        status=status.HTTP_201_CREATED)
