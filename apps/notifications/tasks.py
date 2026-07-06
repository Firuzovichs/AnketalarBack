from celery import shared_task
from django.conf import settings


@shared_task(bind=True, max_retries=3)
def send_notification_task(self, user_id, notif_type, title, body, data=None):
    """
    1. DB ga saqlaydi
    2. FCM push jo'natadi
    """
    from apps.notifications.models import Notification
    from apps.users.models import User

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return

    notif = Notification.objects.create(
        user=user,
        notification_type=notif_type,
        title=title,
        body=body,
        data=data or {},
    )

    # FCM push notification (ixtiyoriy)
    _send_fcm(user, title, body, data or {})

    return notif.id


def _send_fcm(user, title, body, data):
    """Firebase Cloud Messaging orqali push yuborish."""
    fcm_key = settings.FCM_SERVER_KEY
    if not fcm_key:
        return   # FCM key yo'q, skip

    # TODO: user device token modeliga qo'shish
    # import requests
    # requests.post('https://fcm.googleapis.com/fcm/send', ...)
    pass
