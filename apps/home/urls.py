from django.urls import path
from .views import (
    BannerListView, BannerDetailView, NewsListView, NewsDetailView,
    VipSuggestionsView, StaticPageView,
)

urlpatterns = [
    path('banners/',          BannerListView.as_view(),    name='banner-list'),
    path('banners/<int:pk>/', BannerDetailView.as_view(),  name='banner-detail'),
    path('news/',             NewsListView.as_view(),       name='news-list'),
    path('news/<int:pk>/',    NewsDetailView.as_view(),     name='news-detail'),
    path('suggestions/',      VipSuggestionsView.as_view(), name='vip-suggestions'),
    path('pages/<slug:slug>/', StaticPageView.as_view(),    name='static-page'),
]
