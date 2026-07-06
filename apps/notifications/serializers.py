from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    # iOS AppNotification struct "message" fieldiga map qilamiz
    message = serializers.CharField(source='body', read_only=True)
    # data JSON'dan actor ma'lumotlarini chiqaramiz
    actor_name  = serializers.SerializerMethodField()
    actor_photo = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            'id', 'notification_type', 'title', 'body', 'message',
            'data', 'is_read', 'created_at', 'actor_name', 'actor_photo',
        ]
        read_only_fields = ['id', 'created_at']

    def get_actor_name(self, obj):
        val = obj.data.get('actor_name') if obj.data else None
        print(f"[NOTIF] id={obj.id} type={obj.notification_type} data={obj.data} => actor_name={val}")
        return val

    def get_actor_photo(self, obj):
        return obj.data.get('actor_photo') if obj.data else None
