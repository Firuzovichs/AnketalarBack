from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.permissions import AllowAny
from .models import Country, Region, District
from .serializers import CountrySerializer, RegionSerializer, DistrictSerializer


class CountryViewSet(ReadOnlyModelViewSet):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    permission_classes = [AllowAny]


class RegionViewSet(ReadOnlyModelViewSet):
    serializer_class = RegionSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = Region.objects.all()
        country_id = self.request.query_params.get('country')
        if country_id:
            qs = qs.filter(country_id=country_id)
        return qs


class DistrictViewSet(ReadOnlyModelViewSet):
    serializer_class = DistrictSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = District.objects.all()
        region_id = self.request.query_params.get('region')
        if region_id:
            qs = qs.filter(region_id=region_id)
        return qs
