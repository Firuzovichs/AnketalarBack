from django.contrib import admin
from .models import Country, Region, District


class RegionInline(admin.TabularInline):
    model = Region
    extra = 1
    fields = ['name_uz', 'name_ru', 'name']
    show_change_link = True


class DistrictInline(admin.TabularInline):
    model = District
    extra = 1
    fields = ['name_uz', 'name_ru', 'name']


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display   = ['id', 'name_uz', 'name_ru', 'name', 'code', 'region_count']
    search_fields  = ['name', 'name_uz', 'name_ru', 'code']
    inlines        = [RegionInline]

    def region_count(self, obj):
        return obj.regions.count()
    region_count.short_description = 'Viloyatlar'


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display   = ['id', 'name_uz', 'name_ru', 'name', 'country', 'district_count']
    list_filter    = ['country']
    search_fields  = ['name', 'name_uz', 'name_ru']
    inlines        = [DistrictInline]
    list_select_related = ['country']

    def district_count(self, obj):
        return obj.districts.count()
    district_count.short_description = 'Tumanlar'


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display   = ['id', 'name_uz', 'name_ru', 'name', 'region']
    list_filter    = ['region__country', 'region']
    search_fields  = ['name', 'name_uz', 'name_ru']
    list_select_related = ['region', 'region__country']
