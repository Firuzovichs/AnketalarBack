from django.urls import path
from .views import SearchView, SingleSearchView, MapSearchView

urlpatterns = [
    path('',        SearchView.as_view(),       name='search'),
    path('single/', SingleSearchView.as_view(), name='single-search'),
    path('map/',    MapSearchView.as_view(),    name='search-map'),
]
