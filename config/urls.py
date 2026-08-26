from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from config.media import ranged_media

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    path('api/auth/',          include('apps.users.urls')),
    path('api/locations/',     include('apps.locations.urls')),
    path('api/matches/',       include('apps.matches.urls')),
    path('api/stories/',       include('apps.stories.urls')),
    path('api/chat/',          include('apps.chat.urls')),
    path('api/notifications/', include('apps.notifications.urls')),
    path('api/subscriptions/', include('apps.subscriptions.urls')),
    path('api/search/',        include('apps.search.urls')),
    path('api/home/',          include('apps.home.urls')),
    re_path(r'^media/(?P<path>.*)$', ranged_media, name='ranged-media'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
