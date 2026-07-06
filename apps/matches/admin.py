from django.contrib import admin
from .models import Like, Match

@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ['from_user', 'to_user', 'like_type', 'status', 'created_at']
    list_filter  = ['status', 'like_type']

@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ['user1', 'user2', 'chat_room_link', 'created_at']
    autocomplete_fields = ['user1', 'user2']

    def chat_room_link(self, obj):
        room = getattr(obj, 'chat_room', None)
        return f'ChatRoom #{room.id}' if room else '—'
    chat_room_link.short_description = 'Chat xonasi'
