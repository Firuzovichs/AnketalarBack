from django.urls import path
from .views import SendLikeView, RespondLikeView, ReceivedLikesView, MatchListView, SkipUserView, LikeStatusView

urlpatterns = [
    path('like/',                  SendLikeView.as_view(),      name='send-like'),
    path('like/<int:pk>/respond/', RespondLikeView.as_view(),   name='respond-like'),
    path('like-status/<int:user_id>/', LikeStatusView.as_view(), name='like-status'),
    path('skip/',                  SkipUserView.as_view(),       name='skip-user'),
    path('received/',              ReceivedLikesView.as_view(), name='received-likes'),
    path('',                       MatchListView.as_view(),     name='match-list'),
]
