from django.contrib import admin

from .models import Location, LocationAlias


class LocationAliasInline(admin.TabularInline):
    model = LocationAlias
    extra = 1


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ["official_address", "district", "is_active"]
    list_filter = ["district", "is_active"]
    search_fields = ["official_address"]
    inlines = [LocationAliasInline]


@admin.register(LocationAlias)
class LocationAliasAdmin(admin.ModelAdmin):
    list_display = ["name", "location", "is_active"]
    search_fields = ["name", "location__official_address"]
