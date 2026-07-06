from rest_framework.routers import DefaultRouter
from .views import CountryViewSet, RegionViewSet, DistrictViewSet

router = DefaultRouter()
router.register('countries', CountryViewSet)
router.register('regions', RegionViewSet, basename='region')
router.register('districts', DistrictViewSet, basename='district')

urlpatterns = router.urls
