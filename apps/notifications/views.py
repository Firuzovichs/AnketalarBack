from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Notification
from .serializers import NotificationSerializer


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.request.user.notifications.all()


class MarkAllReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        count = request.user.notifications.filter(is_read=False).update(is_read=True)
        return Response({'detail': f'{count} ta bildirishnoma o\'qildi deb belgilandi.'})


class MarkReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            notif = request.user.notifications.get(pk=pk)
        except Notification.DoesNotExist:
            return Response({'detail': 'Topilmadi.', 'code': 'not_found'}, status=404)
        notif.is_read = True
        notif.save()
        return Response({'detail': 'O\'qildi.'})


class UnreadCountView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = request.user.notifications.filter(is_read=False).count()
        return Response({'unread_count': count})
