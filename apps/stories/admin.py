from django.contrib import admin
from django.utils.html import format_html
from .models import Story, StoryView, StoryReaction


class StoryViewInline(admin.TabularInline):
    model = StoryView
    extra = 0
    readonly_fields = ['viewer', 'viewed_at']
    can_delete = False


class StoryReactionInline(admin.TabularInline):
    model = StoryReaction
    extra = 0
    readonly_fields = ['user', 'sticker', 'created_at']
    can_delete = False


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display  = ['id', 'user', 'media_type', 'preview', 'views_count',
                     'reactions_count', 'is_active', 'created_at']
    list_filter   = ['media_type', 'created_at']
    search_fields = ['user__email', 'user__profile__first_name', 'caption']
    readonly_fields = ['created_at', 'expires_at', 'views_count',
                       'reactions_count', 'is_active', 'preview']
    inlines = [StoryViewInline, StoryReactionInline]

    def preview(self, obj):
        if obj.media and obj.media_type == 'image':
            return format_html(
                '<img src="{}" style="height:60px;border-radius:6px;" />',
                obj.media.url
            )
        elif obj.media_type == 'video':
            return format_html(
                '<video src="{}" height="60" style="border-radius:6px;" controls></video>',
                obj.media.url
            )
        return '—'
    preview.short_description = 'Media'


@admin.register(StoryView)
class StoryViewAdmin(admin.ModelAdmin):
    list_display  = ['id', 'story', 'viewer', 'viewed_at']
    list_filter   = ['viewed_at']
    search_fields = ['viewer__email', 'story__user__email']


@admin.register(StoryReaction)
class StoryReactionAdmin(admin.ModelAdmin):
    list_display  = ['id', 'story', 'user', 'sticker', 'created_at']
    list_filter   = ['sticker', 'created_at']
    search_fields = ['user__email', 'story__user__email']
