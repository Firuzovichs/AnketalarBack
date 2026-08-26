from django.utils import timezone
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from .models import Banner, News, StaticPage
from .serializers import BannerSerializer, NewsSerializer, StaticPageSerializer
from apps.users.models import User, Block
from apps.users.serializers import UserSerializer


class BannerListView(generics.ListAPIView):
    """GET /api/home/banners/ — faol bannerlar."""
    serializer_class = BannerSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None  # to'g'ridan massiv qaytaradi

    def get_queryset(self):
        return Banner.objects.filter(is_active=True)


class BannerDetailView(generics.RetrieveAPIView):
    """GET /api/home/banners/{id}/ — banner tafsilotlari."""
    serializer_class = BannerSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Banner.objects.filter(is_active=True)


class NewsListView(generics.ListAPIView):
    """GET /api/home/news/ — faol yangiliklar."""
    serializer_class = NewsSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None  # to'g'ridan massiv qaytaradi

    def get_queryset(self):
        return News.objects.filter(is_active=True)


class NewsDetailView(generics.RetrieveAPIView):
    """GET /api/home/news/{id}/ — yangilik tafsilotlari."""
    serializer_class = NewsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return News.objects.filter(is_active=True)


class StaticPageView(generics.RetrieveAPIView):
    """GET /api/home/pages/{slug}/ — Biz haqimizda / Foydalanish shartlari / Maxfiylik siyosati."""
    serializer_class = StaticPageSerializer
    permission_classes = [AllowAny]
    authentication_classes = []   # JWT tekshirilmasin — token bo'lmasa ham ochiq
    lookup_field = 'slug'
    queryset = StaticPage.objects.all()


class VipSuggestionsView(APIView):
    """
    GET /api/home/suggestions/
    VIP/Premium obunasi bor foydalanuvchilar (Smart tavsiyalar).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        try:
            profile = user.profile
        except Exception:
            return Response([])

        # Qarama-qarshi jins, profili to'liq, VIP obuna bor
        opposite = 'F' if profile.gender == 'M' else 'M'
        qs = User.objects.filter(
            is_active=True,
            profile__gender=opposite,
            profile__is_face_verified=True,
            subscription__isnull=False,
        ).exclude(id__in=Block.excluded_user_ids_for(user)).select_related('profile').prefetch_related('photos').distinct()[:10]

        serializer = UserSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)
