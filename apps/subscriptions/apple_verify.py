"""Apple App Store Server Library bilan ishlash uchun yordamchi modul.

Bu yerda ikki narsa bor:

1. `get_verifier()` — `SignedDataVerifier`ni (Apple ildiz sertifikatlari bilan)
   bir marta yasab, keyingi chaqiriqlarda qayta ishlatadi.
2. `apply_transaction(...)` — Apple'dan TO'LIQ server-tomonda tasdiqlangan
   bitta tranzaksiyani o'qib, mos `Plan`ni topib, foydalanuvchining
   `UserSubscription`'ini yangilaydi VA har doim `ApplePurchase` audit
   qatorini yaratadi. Bu — loyihaning umumiy "hech narsa bazadan
   o'chirilmasin" qoidasiga mos append-only yondashuv: eski qatorlar hech
   qachon o'zgartirilmaydi yoki o'chirilmaydi, faqat yangi qator qo'shiladi.

Ishlatilishi: `apps/subscriptions/views.py` (VerifyPurchaseView — ilovadan
kelgan xarid; AppleServerNotificationView — Apple serverining bildirishnomasi).
"""
import datetime

from django.conf import settings

from appstoreserverlibrary.models.Environment import Environment
from appstoreserverlibrary.signed_data_verifier import SignedDataVerifier

_verifier = None


def get_verifier():
    """`SignedDataVerifier`ni "lazy" tarzda (faqat birinchi chaqiriqda) yasab,
    keyin global o'zgaruvchida saqlab qo'yadi — har bir so'rovda sertifikat
    fayllarini diskdan qayta o'qimaslik uchun."""
    global _verifier
    if _verifier is None:
        certs_dir = settings.APPLE_ROOT_CERTS_DIR
        root_certificates = []
        if certs_dir.is_dir():
            for cert_file in sorted(certs_dir.glob('*.cer')):
                root_certificates.append(cert_file.read_bytes())

        environment = (
            Environment.PRODUCTION if settings.APPLE_ENVIRONMENT == 'Production' else Environment.SANDBOX
        )
        _verifier = SignedDataVerifier(
            root_certificates=root_certificates,
            enable_online_checks=True,
            environment=environment,
            bundle_id=settings.APPLE_BUNDLE_ID,
            app_apple_id=settings.APPLE_APP_APPLE_ID,
        )
    return _verifier


def ms_to_datetime(ms):
    """Apple barcha sanalarni millisekundlardagi UNIX vaqti sifatida beradi."""
    if ms is None:
        return None
    return datetime.datetime.fromtimestamp(ms / 1000, tz=datetime.timezone.utc)


def apply_transaction(transaction, raw_jws, *, source, user=None, notification_type=''):
    """Tasdiqlangan `transaction` (JWSTransactionDecodedPayload) asosida
    foydalanuvchining obunasini yangilaydi va har doim audit qatorini yozadi.

    - `user` berilmagan bo'lsa (Apple serverining bildirishnomasi holati),
      avval shu tranzaksiyaning `originalTransactionId`si bo'yicha qaysi
      foydalanuvchiga tegishli ekanini DB'dan qidiradi (bu maydon
      VerifyPurchaseView orqali ilovadan birinchi marta xarid tasdiqlanganda
      yoziladi).
    - Mahsulot ID'si hali biron Plan'ga bog'lanmagan bo'lsa (admin panelda
      `apple_product_id` to'ldirilmagan), tranzaksiya o'zi haqiqiy bo'lsa ham
      `unknown_apple_product` xatosi bilan belgilanadi — obuna o'zgarmaydi,
      lekin to'lovning o'zi audit jurnaliga yoziladi (yo'qolib ketmaydi).
    - Tranzaksiya bekor qilingan/qaytarilgan bo'lsa (`revocationDate` mavjud),
      foydalanuvchi Free tarifga qaytariladi.
    """
    from .models import ApplePurchase, Plan, UserSubscription

    original_transaction_id = transaction.originalTransactionId or ''

    if user is None and original_transaction_id:
        existing = (
            UserSubscription.objects.filter(apple_original_transaction_id=original_transaction_id)
            .select_related('user')
            .first()
        )
        if existing is not None:
            user = existing.user

    expires_at = ms_to_datetime(transaction.expiresDate)
    is_revoked = transaction.revocationDate is not None
    plan = Plan.objects.filter(apple_product_id=transaction.productId).first() if transaction.productId else None

    error_message = ''
    if plan is None and transaction.productId and not is_revoked:
        error_message = 'unknown_apple_product'

    if user is not None:
        if plan is not None and not is_revoked:
            UserSubscription.objects.update_or_create(
                user=user,
                defaults={
                    'plan': plan,
                    'expires_at': expires_at,
                    'apple_original_transaction_id': original_transaction_id,
                },
            )
        elif is_revoked:
            free_plan = Plan.objects.filter(plan_type='free').first()
            if free_plan is not None:
                UserSubscription.objects.update_or_create(
                    user=user,
                    defaults={'plan': free_plan, 'expires_at': None},
                )

    return ApplePurchase.objects.create(
        user=user,
        source=source,
        notification_type=notification_type,
        product_id=transaction.productId or '',
        transaction_id=transaction.transactionId or '',
        original_transaction_id=original_transaction_id,
        environment=transaction.rawEnvironment or '',
        expires_at=expires_at,
        is_valid=not is_revoked and not error_message,
        error_message=error_message,
        raw_payload={'jws': raw_jws},
    )
