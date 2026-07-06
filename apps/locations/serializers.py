from rest_framework import serializers
from .models import Country, Region, District


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ['id', 'name', 'name_uz', 'name_ru', 'code']


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ['id', 'name', 'name_uz', 'name_ru', 'country']


class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = ['id', 'name', 'name_uz', 'name_ru', 'region']
