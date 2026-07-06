import random
from datetime import date
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

from apps.users.models import User, Block
from apps.users.serializers import UserSerializer
from apps.matches.models import Like
from utils.helpers import calculate_age, haversine_distance, birth_date_from_age
from utils.pagination import StandardPagination


def exclude_already_interacted(qs, user):
    """Allaqachon like yoki match bo'lganlarni chiqarish."""
    liked_ids = Like.objects.filter(from_user=user).values_list('to_user_id', flat=True)
    return qs.exclude(id__in=liked_ids).exclude(id=user.id)


def build_base_queryset(user):
    """Qarama-qarshi jins, active, profili to'liq. Bloklangan (ikki tomonlama)
    foydalanuvchilar BUTUNLAY chiqarib tashlanadi — qidiruv, xarita va
    "Like" tabida ham ko'rinmasinlar."""
    profile = user.profile
    opposite = 'F' if profile.gender == 'M' else 'M'
    return User.objects.filter(
        is_active=True,
        profile__gender=opposite,
        profile__is_face_verified=True,
    ).exclude(id__in=Block.excluded_user_ids_for(user)).select_related('profile').prefetch_related('photos')


def apply_age_range(qs, user_profile):
    """Default yosh diapazoni (filter berilmasa)."""
    age = user_profile.age
    today = date.today()
    if user_profile.gender == 'M':
        # Erkak: 18 dan boshlab, o'zidan 10 yosh kichikdan 10 yosh kattagacha
        min_age, max_age = max(18, age - 10), age + 10
    else:
        # Ayol: 18 dan boshlab, o'zidan 10 yosh kichikdan 10 yosh kattagacha
        min_age, max_age = max(18, age - 10), age + 10

    min_birth = today.replace(year=today.year - max_age)
    max_birth = today.replace(year=today.year - min_age)
    return qs.filter(profile__birth_date__range=[min_birth, max_birth])


def apply_common_filters(qs, params):
    """
    SearchView, MapSearchView va SingleSearchView uchun UMUMIY filtrlar:
    yosh (aniq berilgan bo'lsa), bo'y, vazn, qiziqishlar, maqsadlar,
    davlat/viloyat/tuman. Bu yerda radius YO'Q — radius har bir view'da
    boshqacha markazga ega (xaritada bosilgan nuqta / o'z profili),
    shuning uchun alohida qo'llaniladi.
    """
    if params.get('min_age'):
        today = date.today()
        max_birth = today.replace(year=today.year - int(params['min_age']))
        qs = qs.filter(profile__birth_date__lte=max_birth)
    if params.get('max_age'):
        today = date.today()
        min_birth = today.replace(year=today.year - int(params['max_age']))
        qs = qs.filter(profile__birth_date__gte=min_birth)

    if params.get('min_height'):
        qs = qs.filter(profile__height__gte=int(params['min_height']))
    if params.get('max_height'):
        qs = qs.filter(profile__height__lte=int(params['max_height']))

    if params.get('min_weight'):
        qs = qs.filter(profile__weight__gte=int(params['min_weight']))
    if params.get('max_weight'):
        qs = qs.filter(profile__weight__lte=int(params['max_weight']))

    if params.get('interests'):
        ids = [int(i) for i in params['interests'].split(',') if i.isdigit()]
        if ids:
            qs = qs.filter(profile__interests__in=ids).distinct()

    if params.get('goals'):
        ids = [int(i) for i in params['goals'].split(',') if i.isdigit()]
        if ids:
            qs = qs.filter(profile__goals__in=ids).distinct()

    if params.get('country_id'):
        qs = qs.filter(profile__district__region__country_id=params['country_id'])
    if params.get('region_id'):
        qs = qs.filter(profile__district__region_id=params['region_id'])
    if params.get('district_id'):
        qs = qs.filter(profile__district_id=params['district_id'])

    return qs


def has_explicit_age_filter(params):
    return bool(params.get('min_age') or params.get('max_age'))


def check_radius_permission(user):
    """Profil markazli radius filtri — faqat Premium/VIP."""
    sub = getattr(user, 'subscription', None)
    plan = sub.plan if sub and sub.is_active else None
    return bool(plan and plan.can_use_radius_filter)


def filter_by_profile_radius(users, profile, radius_km):
    """Foydalanuvchining O'Z profilidagi lat/lng markazidan radius (km) bo'yicha."""
    if not (profile.latitude and profile.longitude):
        return users
    lat, lon = float(profile.latitude), float(profile.longitude)
    return [
        u for u in users
        if u.profile.latitude and u.profile.longitude and
        haversine_distance(lat, lon, float(u.profile.latitude), float(u.profile.longitude)) <= radius_km
    ]


class SearchView(APIView):
    """
    GET /api/search/
    Query params:
      min_age, max_age     — yosh oralig'i
      min_height, max_height
      min_weight, max_weight
      interests            — vergul bilan: 1,2,3
      goals                — vergul bilan: 1,2
      district_id
      radius_km            — (Premium+) lat/long radius (km)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        try:
            profile = user.profile
        except Exception:
            return Response({'detail': 'Avval profilingizni to\'ldiring.', 'code': 'profile_incomplete'}, status=400)

        params = request.query_params

        # Radius filter — faqat Premium+
        radius_km = params.get('radius_km')
        if radius_km and not check_radius_permission(user):
            return Response({'detail': 'Radius filter Premium/VIP uchun.', 'code': 'radius_premium_only'}, status=403)

        qs = build_base_queryset(user)
        qs = exclude_already_interacted(qs, user)
        qs = apply_common_filters(qs, params)
        if not has_explicit_age_filter(params):
            qs = apply_age_range(qs, profile)

        # Tartiblash
        ordering = params.get('ordering', 'recommended')
        if ordering == 'newest':
            qs = qs.order_by('-created_at')
        elif ordering == 'nearby':
            qs = qs.order_by('-subscription__plan__price_monthly', 'profile__district')
        else:  # recommended (default)
            qs = qs.order_by('-subscription__plan__price_monthly', '-profile__updated_at')

        users = list(qs)

        # Radius filter (Python darajasida — PostGIS yo'q), o'z profili markazidan
        if radius_km:
            users = filter_by_profile_radius(users, profile, float(radius_km))

        paginator = StandardPagination()
        page = paginator.paginate_queryset(users, request)
        serializer = UserSerializer(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)


class MapSearchView(APIView):
    """
    GET /api/search/map/
    Yandex xarita uchun — atrofdagi foydalanuvchilarni qaytaradi.
    Radius filtri BEPUL (Premium talab qilinmaydi).

    Query params:
      lat, lng              — (majburiy) xaritaning markazi
      radius_km             — standart 10
      min_age, max_age
      min_height, max_height
      min_weight, max_weight
      interests             — vergul bilan: 1,2,3
      goals                 — vergul bilan: 1,2
      country_id
      region_id
      district_id
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        try:
            profile = user.profile
        except Exception:
            return Response({'detail': 'Avval profilingizni to\'ldiring.', 'code': 'profile_incomplete'}, status=400)

        params = request.query_params

        lat_raw = params.get('lat')
        lng_raw = params.get('lng')
        if not lat_raw or not lng_raw:
            return Response({'detail': 'lat va lng majburiy.', 'code': 'latlng_required'}, status=400)
        try:
            center_lat = float(lat_raw)
            center_lng = float(lng_raw)
        except ValueError:
            return Response({'detail': 'lat/lng noto\'g\'ri formatda.', 'code': 'latlng_invalid'}, status=400)

        try:
            radius_km = float(params.get('radius_km', 10))
        except ValueError:
            radius_km = 10.0

        # Xaritada faqat jins bo'yicha filtr (build_base_queryset) qo'llanadi —
        # like yoki match bo'lganlar ham xaritadan chiqarib tashlanmaydi.
        qs = build_base_queryset(user)
        qs = apply_common_filters(qs, params)

        # Faqat koordinatasi borlar
        qs = qs.exclude(profile__latitude__isnull=True).exclude(profile__longitude__isnull=True)

        candidates = list(qs)

        # Radius — Python darajasida (PostGIS yo'q), hammaga bepul
        nearby = []
        for u in candidates:
            try:
                u_lat = float(u.profile.latitude)
                u_lng = float(u.profile.longitude)
            except (TypeError, ValueError):
                continue
            dist = haversine_distance(center_lat, center_lng, u_lat, u_lng)
            if dist <= radius_km:
                nearby.append((dist, u))

        nearby.sort(key=lambda pair: pair[0])
        users = [u for _, u in nearby[:200]]

        serializer = UserSerializer(users, many=True, context={'request': request})
        return Response(serializer.data)


class SingleSearchView(APIView):
    """
    GET /api/search/single/
    Bitta odamni qaytaradi (Tinder-style "Like" tab uchun).
    "Qidirish" (xarita) tabidagi bilan bir xil filtrlarni qabul qiladi:
      min_age, max_age, min_height, max_height, min_weight, max_weight,
      interests, goals, country_id, region_id, district_id,
      radius_km — (Premium+) o'z profil joylashuvidan masofa bo'yicha.
    Filtr berilmasa — standart yosh oralig'i (apply_age_range) qo'llanadi.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        try:
            profile = user.profile
        except Exception:
            return Response({'detail': 'Profil topilmadi.', 'code': 'profile_incomplete'}, status=400)

        params = request.query_params
        radius_km = params.get('radius_km')
        if radius_km and not check_radius_permission(user):
            return Response({'detail': 'Radius filter Premium/VIP uchun.', 'code': 'radius_premium_only'}, status=403)

        qs = build_base_queryset(user)
        qs = exclude_already_interacted(qs, user)
        qs = apply_common_filters(qs, params)
        if not has_explicit_age_filter(params):
            qs = apply_age_range(qs, profile)

        if radius_km:
            # Radius — Python darajasida hisoblanadi, shuning uchun avval
            # ro'yxatga aylantirib, keyin tasodifiy birini tanlaymiz.
            candidates = filter_by_profile_radius(list(qs), profile, float(radius_km))
            candidate = random.choice(candidates) if candidates else None
        else:
            # VIP profili borlar birinchi, qolganlari orasida tasodifiy
            qs = qs.order_by('-subscription__plan__price_monthly', '?')
            candidate = qs.first()

        if not candidate:
            return Response({'detail': 'Hozircha mos kandidat yo\'q.', 'code': 'no_candidates'}, status=404)

        return Response(UserSerializer(candidate, context={'request': request}).data)
