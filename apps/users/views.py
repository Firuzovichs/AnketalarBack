import hashlib
from datetime import timedelta
from django.utils import timezone
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.db.models import Q

from .models import User, UserProfile, UserPhoto, OTPVerification, Interest, Goal, Block, Report, AccountDeletionRequest, TermsAcceptance
from apps.home.models import StaticPage
from .serializers import (
    SendOTPSerializer, VerifyOTPSerializer, RegisterSerializer,
    LoginSerializer, UserSerializer, ProfileSetupSerializer,
    FaceScanSerializer, PhotoUploadSerializer,
    InterestSerializer, GoalSerializer, UserPhotoSerializer,
)
from utils.helpers import generate_otp
from django.conf import settings


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {'refresh': str(refresh), 'access': str(refresh.access_token)}


class SendOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        ser = SendOTPSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        identifier = ser.validated_data['identifier']

        # Allaqachon ro'yxatdan o'tgan foydalanuvchini tekshirish
        from django.db.models import Q
        if User.objects.filter(Q(email=identifier) | Q(phone=identifier)).exists():
            return Response(
                {'detail': 'Bu email yoki telefon raqam allaqachon ro\'yxatdan o\'tgan. Kirish sahifasidan foydalaning.',
                 'code': 'already_registered'},
                status=400
            )

        otp = generate_otp()
        expires = timezone.now() + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)
        OTPVerification.objects.create(identifier=identifier, otp=otp, expires_at=expires)

        # TODO: SMS yoki Email jo'natish (Twilio / SendGrid)
        print(f"[DEV] OTP for {identifier}: {otp}")   # Dev uchun

        return Response({'detail': f'OTP {identifier} ga yuborildi.'})


class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        ser = VerifyOTPSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        record = OTPVerification.objects.filter(
            identifier=ser.validated_data['identifier'],
            otp=ser.validated_data['otp'],
        ).order_by('-created_at').first()
        if not record or not record.is_valid():
            return Response({'detail': 'OTP noto\'g\'ri yoki muddati o\'tgan.', 'code': 'otp_invalid'}, status=400)
        return Response({'detail': 'OTP tasdiqlandi.'})


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        ser = RegisterSerializer(data=request.data, context={'request': request})
        ser.is_valid(raise_exception=True)
        user = ser.save()
        return Response({'tokens': get_tokens_for_user(user), 'user': UserSerializer(user, context={'request': request}).data},
                        status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        ser = LoginSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        identifier = ser.validated_data['identifier']
        password = ser.validated_data['password']

        is_email = '@' in identifier
        try:
            user = User.objects.get(email=identifier) if is_email else User.objects.get(phone=identifier)
        except User.DoesNotExist:
            return Response({'detail': 'Foydalanuvchi topilmadi.', 'code': 'user_not_found'}, status=400)

        if not user.check_password(password):
            return Response({'detail': 'Parol noto\'g\'ri.', 'code': 'wrong_password'}, status=400)
        if not user.is_active:
            return Response({'detail': 'Hisob bloklangan.', 'code': 'account_blocked'}, status=403)

        user.last_seen = timezone.now()
        user.save(update_fields=['last_seen'])
        return Response({'tokens': get_tokens_for_user(user), 'user': UserSerializer(user, context={'request': request}).data})


class TermsStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user, context={'request': request}).data.get('terms_status', {}))


class TermsAcceptView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            terms = StaticPage.objects.get(slug='terms')
        except StaticPage.DoesNotExist:
            return Response({'detail': 'Foydalanish shartlari mavjud emas.'}, status=404)

        requested_version = str(request.data.get('terms_version', ''))
        if requested_version != terms.version:
            return Response({
                'detail': "Foydalanish shartlari yangilangan. Sahifani qayta yuklang.",
                'terms_version': terms.version,
            }, status=409)

        acceptance, _ = TermsAcceptance.objects.get_or_create(
            user=request.user,
            version=terms.version,
            content_hash=hashlib.sha256(terms.content.encode('utf-8')).hexdigest(),
            defaults={
                'ip_address': request.META.get('REMOTE_ADDR'),
                'user_agent': request.META.get('HTTP_USER_AGENT', '')[:500],
            },
        )
        return Response({
            'accepted': True,
            'accepted_at': acceptance.accepted_at,
            'terms_version': acceptance.version,
        })


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        self.request.user.last_seen = timezone.now()
        self.request.user.save(update_fields=['last_seen'])
        return self.request.user


class ProfileSetupView(APIView):
    permission_classes = [IsAuthenticated]

    def _save(self, request):
        # Avval validatsiya, keyin create/update
        try:
            profile = UserProfile.objects.get(user=request.user)
            ser = ProfileSetupSerializer(profile, data=request.data, partial=True)
        except UserProfile.DoesNotExist:
            ser = ProfileSetupSerializer(data=request.data)

        ser.is_valid(raise_exception=True)
        profile = ser.save(user=request.user)
        return Response(UserSerializer(request.user, context={'request': request}).data)

    def post(self, request):
        return self._save(request)

    def patch(self, request):
        return self._save(request)

    def put(self, request):
        return self._save(request)


class FaceScanView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        ser = FaceScanSerializer(profile, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response({'detail': 'Yuz skaneri saqlandi va tasdiqlandi.', 'is_face_verified': True})


class PhotoUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        photos = request.user.photos.filter(is_deleted=False)
        return Response(UserPhotoSerializer(photos, many=True, context={'request': request}).data)

    def post(self, request):
        ser = PhotoUploadSerializer(data=request.data, context={'request': request})
        ser.is_valid(raise_exception=True)
        photo = ser.save()
        return Response(UserPhotoSerializer(photo, context={'request': request}).data,
                        status=status.HTTP_201_CREATED)


class PhotoDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        """Soft delete — DB dan o'chmaydi, faqat is_deleted=True (Story bilan bir xil konvensiya)."""
        try:
            photo = request.user.photos.get(pk=pk, is_deleted=False)
        except UserPhoto.DoesNotExist:
            return Response({'detail': 'Rasm topilmadi.', 'code': 'photo_not_found'}, status=404)

        was_main = photo.is_main
        photo.is_deleted = True
        photo.is_main = False
        photo.save(update_fields=['is_deleted', 'is_main'])

        # Asosiy rasm o'chirilgan bo'lsa — keyingisini asosiy qilamiz
        if was_main:
            next_photo = request.user.photos.filter(is_deleted=False).order_by('order').first()
            if next_photo:
                next_photo.is_main = True
                next_photo.save(update_fields=['is_main'])

        return Response(status=status.HTTP_204_NO_CONTENT)


class InterestListView(generics.ListAPIView):
    queryset = Interest.objects.all()
    serializer_class = InterestSerializer
    permission_classes = [AllowAny]


class GoalListView(generics.ListAPIView):
    queryset = Goal.objects.all()
    serializer_class = GoalSerializer
    permission_classes = [AllowAny]


# ── Parolni tiklash ──────────────────────────────────────────────────

class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        identifier = request.data.get('identifier', '').strip()
        if not identifier:
            return Response({'detail': "Email yoki telefon raqam kiriting.", 'code': 'identifier_required'}, status=400)

        user = User.objects.filter(Q(email=identifier) | Q(phone=identifier)).first()
        if not user:
            return Response({'detail': "Bu email yoki telefon raqam ro'yxatdan o'tmagan.", 'code': 'not_registered'}, status=404)

        otp_code = generate_otp()
        expires = timezone.now() + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)
        OTPVerification.objects.create(identifier=identifier, otp=otp_code, expires_at=expires)

        # TODO: haqiqiy email/SMS yuborish
        # Hozircha debug rejimida kodni javobda qaytaramiz
        response_data = {'detail': f"OTP yuborildi: {identifier}"}
        if settings.DEBUG:
            response_data['debug_otp'] = otp_code
        return Response(response_data)


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        identifier = request.data.get('identifier', '').strip()
        otp_code = request.data.get('otp', '').strip()
        new_password = request.data.get('new_password', '')

        if not identifier or not otp_code or not new_password:
            return Response({'detail': "Barcha maydonlarni to'ldiring.", 'code': 'fill_all_fields'}, status=400)

        if len(new_password) < 6:
            return Response({'detail': "Parol kamida 6 ta belgi bo'lishi kerak.", 'code': 'password_too_short'}, status=400)

        record = OTPVerification.objects.filter(
            identifier=identifier, otp=otp_code, is_used=False
        ).order_by('-created_at').first()

        if not record or not record.is_valid():
            return Response({'detail': "OTP noto'g'ri yoki muddati o'tgan.", 'code': 'otp_invalid'}, status=400)

        user = User.objects.filter(Q(email=identifier) | Q(phone=identifier)).first()
        if not user:
            return Response({'detail': "Foydalanuvchi topilmadi.", 'code': 'user_not_found'}, status=404)

        user.set_password(new_password)
        user.save()
        record.is_used = True
        record.save()

        return Response({'detail': "Parol muvaffaqiyatli o'zgartirildi. Qayta kiring."})


# ── Boshqa foydalanuvchi profili ─────────────────────────────────────

class UserDetailView(generics.RetrieveAPIView):
    """GET /auth/users/<pk>/ — boshqa foydalanuvchi profilini ko'rish."""
    serializer_class   = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        from django.contrib.auth import get_user_model
        return get_user_model().objects.filter(is_active=True)


# ── Bloklash + adminga shikoyat ───────────────────────────────────────

class BlockUserView(APIView):
    """Foydalanuvchini bloklash. Shu bilan birga (bitta amal sifatida)
    adminga ko'rinadigan `Report` yozuvi ham yaratiladi — alohida shikoyat
    endpointi yo'q, "bloklash + bildirgi" birgalikda ishlaydi."""
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        if user_id == request.user.id:
            return Response({'detail': "O'zingizni bloklay olmaysiz.", 'code': 'cant_block_self'}, status=400)

        try:
            target = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({'detail': 'Foydalanuvchi topilmadi.', 'code': 'user_not_found'}, status=404)

        block, created = Block.objects.get_or_create(
            user=request.user, blocked_user=target, defaults={'is_active': True}
        )
        if not created and not block.is_active:
            block.is_active = True
            block.save(update_fields=['is_active'])

        reason = request.data.get('reason', 'other')
        valid_reasons = {choice[0] for choice in Report.REASON_CHOICES}
        if reason not in valid_reasons:
            reason = 'other'
        description = request.data.get('description', '')

        Report.objects.create(
            reporter=request.user, reported_user=target,
            reason=reason, description=description,
        )

        return Response({'detail': 'Foydalanuvchi bloklandi.', 'blocked_user_id': target.id})


class UnblockUserView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        # MUHIM: bazadan o'chirilmaydi — faqat is_active=False qilinadi.
        Block.objects.filter(
            user=request.user, blocked_user_id=user_id, is_active=True
        ).update(is_active=False)
        return Response({'detail': 'Foydalanuvchi blokdan chiqarildi.'})


class AccountDeletionRequestView(APIView):
    """
    GET  /api/auth/account/delete-request/ — eng so'nggi so'rov holatini qaytaradi (yoki null).
    POST /api/auth/account/delete-request/ — yangi o'chirish so'rovini yuboradi.

    MUHIM: bu yerda hisob ham, so'rov ham bazadan hech qachon o'chirilmaydi —
    admin panelda tasdiqlansa, `AccountDeletionRequest.approve()` faqat
    `user.is_active=False` qiladi (LoginView buni allaqachon tekshiradi).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        req = AccountDeletionRequest.objects.filter(user=request.user).order_by('-created_at').first()
        if not req:
            return Response({'status': None})
        return Response({
            'status': req.status,
            'created_at': req.created_at,
            'reviewed_at': req.reviewed_at,
        })

    def post(self, request):
        existing = AccountDeletionRequest.objects.filter(user=request.user, status='pending').first()
        if existing:
            return Response({'detail': "So'rovingiz allaqachon yuborilgan, ko'rib chiqilmoqda.", 'status': 'pending'}, status=200)

        reason = request.data.get('reason', '')
        req = AccountDeletionRequest.objects.create(user=request.user, reason=reason)
        return Response({'detail': "So'rov yuborildi, admin ko'rib chiqadi.", 'status': req.status}, status=201)
