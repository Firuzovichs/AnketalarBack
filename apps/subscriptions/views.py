from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import generics

from appstoreserverlibrary.signed_data_verifier import VerificationException

from . import apple_verify
from .models import ApplePurchase, Plan, UserSubscription
from .serializers import PlanSerializer, UserSubscriptionSerializer


class PlanListView(generics.ListAPIView):
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer
    permission_classes = [AllowAny]


class MySubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            sub = request.user.subscription
            return Response(UserSubscriptionSerializer(sub).data)
        except UserSubscription.DoesNotExist:
            free_plan = Plan.objects.filter(plan_type='free').first()
            return Response({'plan': PlanSerializer(free_plan).data, 'is_active': True})


class VerifyPurchaseView(APIView):
    """iOS ilova StoreKit orqali xarid qilgandan/yangilagandan keyin shu yerga
    `signed_transaction` (StoreKit'dagi `Transaction.jwsRepresentation`)
    yuboradi. Biz buni Apple'ning rasmiy `app-store-server-library` kutubxonasi
    orqali TO'LIQ server-tomonda tekshiramiz — faqat ilovaga (mijozga)
    ishonib qolmaymiz, chunki mijoz tomonidagi ma'lumotni soxtalashtirish
    mumkin."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        signed_transaction = request.data.get('signed_transaction')
        if not signed_transaction:
            return Response(
                {'detail': "signed_transaction majburiy.", 'code': 'signed_transaction_required'},
                status=400,
            )

        try:
            transaction = apple_verify.get_verifier().verify_and_decode_signed_transaction(signed_transaction)
        except VerificationException:
            ApplePurchase.objects.create(
                user=request.user,
                source='device_verify',
                is_valid=False,
                error_message='verification_failed',
                raw_payload={'jws': signed_transaction},
            )
            return Response(
                {'detail': "Xaridni tasdiqlash imkonsiz.", 'code': 'apple_verification_failed'},
                status=400,
            )

        purchase = apple_verify.apply_transaction(
            transaction, signed_transaction, source='device_verify', user=request.user,
        )

        if purchase.error_message == 'unknown_apple_product':
            return Response(
                {'detail': "Bu mahsulot hali tizimda tanilmagan.", 'code': 'unknown_apple_product'},
                status=400,
            )

        try:
            sub = request.user.subscription
            return Response(UserSubscriptionSerializer(sub).data)
        except UserSubscription.DoesNotExist:
            return Response({'detail': 'OK'})


class AppleServerNotificationView(APIView):
    """Apple App Store Server Notifications V2 — Apple obuna
    yangilanganda/bekor qilinganda/muddati tugaganda shu manzilga avtomatik
    POST yuboradi (App Store Connect > App Information > App Store Server
    Notifications bo'limida sozlanadi). AllowAny: bu so'rov Apple'dan kelади
    va bizning JWT bilan emas — buning o'rniga `signedPayload`ning o'zi
    Apple tomonidan imzolangan va shu yerda tekshiriladi."""
    permission_classes = [AllowAny]

    def post(self, request):
        signed_payload = request.data.get('signedPayload')
        if not signed_payload:
            return Response(status=400)

        verifier = apple_verify.get_verifier()
        try:
            notification = verifier.verify_and_decode_notification(signed_payload)
        except VerificationException:
            ApplePurchase.objects.create(
                source='server_notification',
                is_valid=False,
                error_message='verification_failed',
                raw_payload={'jws': signed_payload},
            )
            return Response(status=400)

        notification_type = notification.rawNotificationType or ''

        if notification.data and notification.data.signedTransactionInfo:
            try:
                transaction = verifier.verify_and_decode_signed_transaction(
                    notification.data.signedTransactionInfo
                )
            except VerificationException:
                ApplePurchase.objects.create(
                    source='server_notification',
                    notification_type=notification_type,
                    is_valid=False,
                    error_message='verification_failed',
                    raw_payload={'jws': signed_payload},
                )
                return Response(status=400)

            apple_verify.apply_transaction(
                transaction, notification.data.signedTransactionInfo,
                source='server_notification', notification_type=notification_type,
            )
        else:
            # Tranzaksiya ma'lumoti bo'lmagan bildirishnoma (masalan Apple'ning
            # test xabari) — baribir audit jurnaliga yozib qo'yamiz.
            ApplePurchase.objects.create(
                source='server_notification',
                notification_type=notification_type,
                raw_payload={'jws': signed_payload},
            )

        return Response(status=200)
