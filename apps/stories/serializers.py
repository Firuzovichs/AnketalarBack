from rest_framework import serializers
from .models import Story, StoryView, StoryReaction
from apps.users.serializers import UserSerializer


class StoryReactionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = StoryReaction
        fields = ['id', 'user', 'sticker', 'created_at']


class StoryViewSerializer(serializers.ModelSerializer):
    viewer   = UserSerializer(read_only=True)
    reaction = serializers.SerializerMethodField()

    class Meta:
        model = StoryView
        fields = ['id', 'viewer', 'viewed_at', 'reaction']

    def get_reaction(self, obj):
        try:
            # story_id ishlatamiz — lazy load yo'q
            r = StoryReaction.objects.get(story_id=obj.story_id, user_id=obj.viewer_id)
            print(f"[VIEWERS] viewer={obj.viewer_id} sticker={r.sticker}")
            return r.sticker
        except StoryReaction.DoesNotExist:
            print(f"[VIEWERS] no reaction: viewer={obj.viewer_id} story={obj.story_id}")
            return None
        except Exception as e:
            print(f"[VIEWERS] get_reaction ERROR: {e}")
            return None


class StorySerializer(serializers.ModelSerializer):
    user           = UserSerializer(read_only=True)
    views_count    = serializers.IntegerField(read_only=True)
    reactions_count = serializers.IntegerField(read_only=True)
    is_active      = serializers.BooleanField(read_only=True)
    is_viewed      = serializers.SerializerMethodField()
    my_reaction    = serializers.SerializerMethodField()

    class Meta:
        model = Story
        fields = [
            'id', 'user', 'media', 'media_type', 'caption',
            'created_at', 'expires_at', 'is_active',
            'views_count', 'reactions_count',
            'is_viewed', 'my_reaction',
        ]
        read_only_fields = ['created_at', 'expires_at']

    def get_is_viewed(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.views.filter(viewer=request.user).exists()

    def get_my_reaction(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        reaction = obj.reactions.filter(user=request.user).first()
        return reaction.sticker if reaction else None


class StoryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Story
        fields = ['media', 'media_type', 'caption']


class ReactToStorySerializer(serializers.Serializer):
    sticker = serializers.CharField(max_length=50)


class ReplyToStorySerializer(serializers.Serializer):
    text = serializers.CharField(max_length=1000, allow_blank=False, trim_whitespace=True)
