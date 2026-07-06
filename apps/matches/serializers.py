from rest_framework import serializers
from .models import Like, Match
from apps.users.serializers import UserSerializer


class LikeSerializer(serializers.ModelSerializer):
    from_user = UserSerializer(read_only=True)
    to_user   = UserSerializer(read_only=True)

    class Meta:
        model = Like
        fields = ['id', 'from_user', 'to_user', 'like_type', 'status', 'message', 'created_at']
        read_only_fields = ['id', 'from_user', 'status', 'message', 'created_at']


class SendLikeSerializer(serializers.Serializer):
    to_user_id = serializers.IntegerField()
    like_type  = serializers.ChoiceField(choices=['like', 'super_like'], default='like')
    # "Habar bilan like" tugmasi bosilganda — ixtiyoriy, bo'sh bo'lishi mumkin.
    message    = serializers.CharField(required=False, allow_blank=True, default='', max_length=500)


class RespondLikeSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['accept', 'reject'])


class MatchSerializer(serializers.ModelSerializer):
    other_user    = serializers.SerializerMethodField()
    has_chat_room = serializers.SerializerMethodField()
    chat_room_id  = serializers.SerializerMethodField()

    class Meta:
        model = Match
        fields = ['id', 'other_user', 'has_chat_room', 'chat_room_id', 'created_at']

    def get_other_user(self, obj):
        request = self.context.get('request')
        other = obj.get_other_user(request.user)
        return UserSerializer(other, context=self.context).data

    def get_has_chat_room(self, obj):
        return hasattr(obj, 'chat_room')

    def get_chat_room_id(self, obj):
        if hasattr(obj, 'chat_room'):
            return obj.chat_room.id
        return None
