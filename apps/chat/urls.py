from django.urls import path
from .views import (
    ChatRoomListView, ChatRoomDetailView, AdminRoomView,
    MessageListView, MessageDetailView, SendMessageView, DeleteMessageView, EditMessageView,
    MarkPhotoViewedView, ScreenshotAlertView,
    ToggleMuteView, ClearChatView, SearchMessagesView,
)

urlpatterns = [
    path('rooms/',                              ChatRoomListView.as_view(),   name='chat-rooms'),
    path('rooms/admin/',                        AdminRoomView.as_view(),      name='chat-admin-room'),
    path('rooms/<int:pk>/',                     ChatRoomDetailView.as_view(), name='chat-room-detail'),
    path('rooms/<int:pk>/mute/',                ToggleMuteView.as_view(),    name='chat-room-mute'),
    path('rooms/<int:pk>/clear/',               ClearChatView.as_view(),     name='chat-room-clear'),
    path('rooms/<int:room_id>/messages/',       MessageListView.as_view(),    name='messages'),
    path('rooms/<int:room_id>/messages/send/',  SendMessageView.as_view(),    name='send-message'),
    path('rooms/<int:room_id>/messages/search/', SearchMessagesView.as_view(), name='search-messages'),
    path('messages/<int:pk>/',                  MessageDetailView.as_view(),  name='message-detail'),
    path('messages/<int:pk>/delete/',           DeleteMessageView.as_view(),  name='delete-message'),
    path('messages/<int:pk>/edit/',             EditMessageView.as_view(),    name='edit-message'),
    path('messages/<int:pk>/view/',             MarkPhotoViewedView.as_view(), name='mark-photo-viewed'),
    path('rooms/<int:room_id>/screenshot-alert/', ScreenshotAlertView.as_view(), name='screenshot-alert'),
]
