from django.utils import timezone
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics, status

from .models import Like, Match
from .serializers import LikeSerializer, SendLikeSerializer, RespondLikeSerializer, MatchSerializer
from apps.users.models import User
from apps.notifications.tasks import send_notification_task


def check_like_limit(user):
    """Kunlik like limitini tekshirish. `limit` qiymati ham qaytariladi —
    iOS tomonida xabar tilga qarab shu son bilan qayta shakllantiriladi
    (backend matni faqat zaxira/fallback sifatida ishlatiladi)."""
    sub = getattr(user, 'subscription', None)
    plan = sub.plan if sub and sub.is_active else None
    limit = plan.likes_per_day if plan else 20
    if limit == -1:
        return True, None, None
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    count = Like.objects.filter(from_user=user, created_at__gte=today_start).count()
    if count >= limit:
        return False, f"Kunlik like limit ({limit}) tugadi.", limit
    return True, None, None


class SendLikeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ser = SendLikeSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        to_user_id = ser.validated_data['to_user_id']
        like_type  = ser.validated_data['like_type']
        message    = (ser.validated_data.get('message') or '').strip()

        if to_user_id == request.user.id:
            return Response({'detail': 'O\'zingizga like qo\'ya olmaysiz.', 'code': 'cant_like_self'}, status=400)

        allowed, msg, limit_val = check_like_limit(request.user)
        if not allowed:
            return Response({'detail': msg, 'code': 'daily_like_limit', 'limit': limit_val}, status=429)

        # Super like tekshirish
        if like_type == 'super_like':
            sub = getattr(request.user, 'subscription', None)
            plan = sub.plan if sub and sub.is_active else None
            sl_limit = plan.super_likes_per_day if plan else 0
            today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
            sl_count = Like.objects.filter(
                from_user=request.user, like_type='super_like', created_at__gte=today_start
            ).count()
            if sl_count >= sl_limit:
                return Response({'detail': 'Super like limit tugadi.', 'code': 'super_like_limit'}, status=429)

        try:
            to_user = User.objects.get(pk=to_user_id)
        except User.DoesNotExist:
            return Response({'detail': 'Foydalanuvchi topilmadi.', 'code': 'user_not_found'}, status=404)

        # Qarama-qarshi tomon avval like bosganmi? (mutual swipe — Tinder uslubidagi avtomatik match)
        reciprocal = Like.objects.filter(
            from_user=to_user, to_user=request.user, status=Like.STATUS_PENDING
        ).first()

        like, created = Like.objects.get_or_create(
            from_user=request.user, to_user=to_user,
            defaults={'like_type': like_type, 'message': message}
        )
        if not created:
            return Response({'detail': 'Allaqachon like qo\'yilgan.', 'code': 'already_liked'}, status=400)

        matched = False
        match_id = None
        chat_room_id = None

        if reciprocal:
            # Ikki tomon ham bir-birini like bosgan — avtomatik match yaratamiz
            like.status = Like.STATUS_ACCEPTED
            like.save(update_fields=['status'])
            reciprocal.status = Like.STATUS_ACCEPTED
            reciprocal.save(update_fields=['status'])

            u1, u2 = sorted([request.user, to_user], key=lambda u: u.id)
            match, match_created = Match.objects.get_or_create(user1=u1, user2=u2)
            # ChatRoom Match'ning post_save signali orqali (apps/matches/signals.py)
            # avtomatik yaratiladi — bu yerda faqat o'qib olamiz.
            room = getattr(match, 'chat_room', None)

            matched = True
            match_id = match.id
            chat_room_id = room.id if room else None

            # "Habar bilan like" — agar ikki tomondan birortasi (yoki ikkisi
            # ham) like bilan birga matn yozgan bo'lsa, shu matn(lar) yangi
            # chat xonasiga BIRINCHI xabar(lar) sifatida ko'chiriladi. Avval
            # ANCHA OLDIN like bosib kutib turgan tomonning xabari (reciprocal),
            # so'ng hozir like bosgan tomonning xabari — vaqt tartibida.
            if room:
                from apps.chat.models import Message
                for liker, text in ((reciprocal.from_user, reciprocal.message),
                                     (request.user, message)):
                    if text:
                        Message.objects.create(
                            room=room, sender=liker,
                            message_type=Message.MSG_TEXT, content=text,
                        )

            send_notification_task.delay(
                user_id=to_user.id,
                notif_type='like_accepted',
                title='Match! 🎉',
                body=f'{request.user.profile.first_name} bilan match bo\'ldingiz!',
                data={'match_id': match.id},
            )
        else:
            # Oddiy like — bildirishnoma jo'natish
            send_notification_task.delay(
                user_id=to_user.id,
                notif_type='new_like',
                title='Yangi like!',
                body=f'{request.user.profile.first_name} sizni yoqtirdi.',
                data={'from_user_id': request.user.id},
            )

        data = LikeSerializer(like, context={'request': request}).data
        data['matched'] = matched
        data['match_id'] = match_id
        data['chat_room_id'] = chat_room_id
        return Response(data, status=status.HTTP_201_CREATED)


class RespondLikeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            like = Like.objects.get(pk=pk, to_user=request.user, status=Like.STATUS_PENDING)
        except Like.DoesNotExist:
            return Response({'detail': 'Like topilmadi.', 'code': 'like_not_found'}, status=404)

        ser = RespondLikeSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        action = ser.validated_data['action']

        if action == 'accept':
            like.status = Like.STATUS_ACCEPTED
            like.save()
            # Match yaratish
            u1, u2 = sorted([like.from_user, request.user], key=lambda u: u.id)
            match, created = Match.objects.get_or_create(user1=u1, user2=u2)
            if created:
                # ChatRoom Match'ning post_save signali orqali avtomatik yaratiladi.
                # Agar asl like "habar bilan" yuborilgan bo'lsa, shu matn yangi
                # xonaga birinchi xabar sifatida ko'chiriladi (SendLikeView'dagi
                # mutual-match holati bilan bir xil mantiq).
                room = getattr(match, 'chat_room', None)
                if room and like.message:
                    from apps.chat.models import Message
                    Message.objects.create(
                        room=room, sender=like.from_user,
                        message_type=Message.MSG_TEXT, content=like.message,
                    )
                # Bildirishnoma
                send_notification_task.delay(
                    user_id=like.from_user.id,
                    notif_type='like_accepted',
                    title='Match! 🎉',
                    body=f'{request.user.profile.first_name} sizning likeni qabul qildi!',
                    data={'match_id': match.id},
                )
            return Response({'detail': 'Qabul qilindi.', 'match_id': match.id})
        else:
            like.status = Like.STATUS_REJECTED
            like.save()
            return Response({'detail': 'Rad etildi.'})


class ReceivedLikesView(generics.ListAPIView):
    serializer_class = LikeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Faqat premium+ ko'ra oladi
        sub = getattr(user, 'subscription', None)
        plan = sub.plan if sub and sub.is_active else None
        can_see = plan.can_see_who_liked if plan else False
        if not can_see:
            return Like.objects.none()
        return Like.objects.filter(to_user=user, status=Like.STATUS_PENDING).select_related('from_user')


class SkipUserView(APIView):
    """
    POST /api/matches/skip/
    body: {"to_user_id": 5}
    Foydalanuvchini o'tkazib yuboradi (dislike).
    Like modeli STATUS_REJECTED sifatida saqlanadi.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        to_user_id = request.data.get('to_user_id')
        if not to_user_id:
            return Response({'detail': 'to_user_id talab qilinadi.', 'code': 'to_user_id_required'}, status=400)
        if to_user_id == request.user.id:
            return Response({'detail': 'O\'zingizni skip qila olmaysiz.', 'code': 'cant_skip_self'}, status=400)
        try:
            to_user = User.objects.get(pk=to_user_id)
        except User.DoesNotExist:
            return Response({'detail': 'Foydalanuvchi topilmadi.', 'code': 'user_not_found'}, status=404)

        Like.objects.get_or_create(
            from_user=request.user, to_user=to_user,
            defaults={'like_type': 'like', 'status': Like.STATUS_REJECTED}
        )
        return Response({'detail': 'O\'tkazib yuborildi.'})


class MatchListView(generics.ListAPIView):
    serializer_class = MatchSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Match.objects.filter(
            Q(user1=user) | Q(user2=user)
        ).select_related('user1', 'user2').prefetch_related('chat_room')


class LikeStatusView(APIView):
    """
    GET /api/matches/like-status/<user_id>/
    Joriy foydalanuvchi ko'rsatilgan odamni avval like bosganmi va ular
    o'rtasida match (demak chat xonasi) mavjudmi — buni OLDINDAN (hali
    qayta like bosishga urinmasdan) bilish uchun. Faqat o'qiydi, hech
    narsani o'zgartirmaydi/o'chirmaydi.

    iOS: UserProfileView ochilganda chaqiriladi — agar `liked` true bo'lsa,
    Like tugmasi o'rniga Bloklash/Chatga o'tish ko'rsatiladi.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        liked = Like.objects.filter(from_user=request.user, to_user_id=user_id).exists()

        match = Match.objects.filter(
            Q(user1=request.user, user2_id=user_id) | Q(user1_id=user_id, user2=request.user)
        ).select_related('chat_room').first()

        matched = match is not None
        chat_room_id = None
        if match is not None:
            room = getattr(match, 'chat_room', None)
            chat_room_id = room.id if room else None

        return Response({'liked': liked, 'matched': matched, 'chat_room_id': chat_room_id})
