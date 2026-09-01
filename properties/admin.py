from django.contrib import admin

from .models import Property


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "listing_type",
        "listing_owner_type",
        "agent",
        "property_type",
        "price",
        "district",
        "is_verified",
        "is_vip",
        "status",
        "is_active",
    ]
    list_filter = ["listing_type", "property_type", "district", "status", "is_verified", "is_vip"]
    search_fields = ["title", "official_address", "district"]
