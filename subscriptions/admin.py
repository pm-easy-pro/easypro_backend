from django.contrib import admin

from .models import Subscription, SubscriptionPackage


@admin.register(SubscriptionPackage)
class SubscriptionPackageAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "target_type",
        "price",
        "billing_period",
        "max_listings",
        "max_vip_listings",
        "is_popular",
        "is_active",
        "sort_order",
    ]
    list_filter = ["target_type", "billing_period", "is_active", "is_popular"]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name", "slug"]


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ["agent", "package", "status", "started_at", "expires_at", "auto_renew"]
    list_filter = ["status", "package__target_type", "auto_renew"]
    search_fields = ["agent__display_name", "agent__company_name", "package__name"]
    raw_id_fields = ["agent", "package"]
