from django.urls import path
from .views import (
    StoryFeedView, StoryCreateView, StoryDetailView,
    MyStoriesView, StoryViewView, StoryViewersView, StoryReactionsView, ReactToStoryView,
    ReplyToStoryView,
)

urlpatterns = [
    path('feed/',                           StoryFeedView.as_view(),       name='story-feed'),
    path('',                                StoryCreateView.as_view(),     name='story-create'),
    path('mine/',                           MyStoriesView.as_view(),       name='my-stories'),
    path('my/',                             MyStoriesView.as_view(),       name='my-stories-alt'),
    path('<int:pk>/',                       StoryDetailView.as_view(),     name='story-detail'),
    path('<int:pk>/view/',                  StoryViewView.as_view(),       name='story-view'),
    path('<int:pk>/viewers/',               StoryViewersView.as_view(),    name='story-viewers'),
    path('<int:pk>/reactions/',             StoryReactionsView.as_view(),  name='story-reactions'),
    path('<int:pk>/react/',                 ReactToStoryView.as_view(),    name='story-react'),
    path('<int:pk>/reply/',                 ReplyToStoryView.as_view(),    name='story-reply'),
]
