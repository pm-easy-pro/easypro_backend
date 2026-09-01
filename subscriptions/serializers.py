from django.utils.text import slugify
from django.utils import timezone
from rest_framework import serializers

from accounts.models import Agent
from properties.models import Property

from .models import Subscription, SubscriptionPackage


class SubscriptionPackageSerializer(serializers.ModelSerializer):
    billing_period_display = serializers.CharField(
        source="get_billing_period_display", read_only=True
    )
    target_type_display = serializers.CharField(
        source="get_target_type_display", read_only=True
    )

    class Meta:
        model = SubscriptionPackage
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "target_type",
            "target_type_display",
            "price",
            "billing_period",
            "billing_period_display",
            "max_listings",
            "max_vip_listings",
            "features",
            "is_popular",
            "sort_order",
        ]


class SubscriptionPackageManageSerializer(serializers.ModelSerializer):
    billing_period_display = serializers.CharField(
        source="get_billing_period_display", read_only=True
    )
    target_type_display = serializers.CharField(
        source="get_target_type_display", read_only=True
    )
    slug = serializers.SlugField(required=False, allow_blank=True)

    class Meta:
        model = SubscriptionPackage
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "target_type",
            "target_type_display",
            "price",
            "billing_period",
            "billing_period_display",
            "max_listings",
            "max_vip_listings",
            "features",
            "is_popular",
            "sort_order",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def _ensure_unique_slug(self, slug, instance=None):
        base = slug
        counter = 1
        qs = SubscriptionPackage.objects.filter(slug=slug)
        if instance:
            qs = qs.exclude(pk=instance.pk)
        while qs.exists():
            slug = f"{base}-{counter}"
            counter += 1
            qs = SubscriptionPackage.objects.filter(slug=slug)
            if instance:
                qs = qs.exclude(pk=instance.pk)
        return slug

    def validate(self, attrs):
        name = attrs.get("name") or (self.instance.name if self.instance else "")
        slug = attrs.get("slug") or slugify(name)
        if not slug:
            raise serializers.ValidationError({"slug": "Slug үүсгэх боломжгүй."})
        attrs["slug"] = self._ensure_unique_slug(slug, self.instance)
        return attrs

    def create(self, validated_data):
        if not validated_data.get("slug"):
            validated_data["slug"] = slugify(validated_data["name"])
        return super().create(validated_data)


class SubscriptionSerializer(serializers.ModelSerializer):
    package = SubscriptionPackageSerializer(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    days_remaining = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = [
            "id",
            "package",
            "status",
            "status_display",
            "started_at",
            "expires_at",
            "auto_renew",
            "cancelled_at",
            "days_remaining",
        ]

    def get_days_remaining(self, obj):
        if obj.expires_at <= timezone.now():
            return 0
        return (obj.expires_at - timezone.now()).days


class SubscriptionUsageSerializer(serializers.Serializer):
    listings_count = serializers.IntegerField()
    vip_listings_count = serializers.IntegerField()
    max_listings = serializers.IntegerField()
    max_vip_listings = serializers.IntegerField()
    listings_remaining = serializers.IntegerField()
    vip_listings_remaining = serializers.IntegerField()


class SubscribeSerializer(serializers.Serializer):
    package_id = serializers.IntegerField()

    def validate_package_id(self, value):
        try:
            package = SubscriptionPackage.objects.get(pk=value, is_active=True)
        except SubscriptionPackage.DoesNotExist:
            raise serializers.ValidationError("Багц олдсонгүй.")
        self.context["package"] = package
        return value

    def validate(self, attrs):
        agent = self.context.get("agent")
        package = self.context["package"]
        if agent.agent_type != package.target_type:
            raise serializers.ValidationError(
                {"package_id": "Энэ багц таны профайлд тохирохгүй байна."}
            )
        return attrs


def get_agent_for_user(user):
    return getattr(user, "agent_profile", None)


def get_subscription_usage(agent, package=None):
    listings_qs = Property.objects.filter(is_active=True, agent=agent)
    listings_count = listings_qs.count()
    vip_count = listings_qs.filter(is_vip=True).count()

    max_listings = package.max_listings if package else 0
    max_vip = package.max_vip_listings if package else 0

    return {
        "listings_count": listings_count,
        "vip_listings_count": vip_count,
        "max_listings": max_listings,
        "max_vip_listings": max_vip,
        "listings_remaining": max(0, max_listings - listings_count) if max_listings else 0,
        "vip_listings_remaining": max(0, max_vip - vip_count) if max_vip else 0,
    }


def get_dashboard_stats(user):
    agent = get_agent_for_user(user)
    subscription = None
    usage = None
    packages_target = None

    if agent:
        subscription = Subscription.get_active_for_agent(agent)
        usage = get_subscription_usage(agent, subscription.package if subscription else None)
        packages_target = agent.agent_type
    else:
        listings_qs = Property.objects.filter(is_active=True, posted_by=user)
        usage = {
            "listings_count": listings_qs.count(),
            "vip_listings_count": listings_qs.filter(is_vip=True).count(),
            "max_listings": 3,
            "max_vip_listings": 0,
            "listings_remaining": max(0, 3 - listings_qs.count()),
            "vip_listings_remaining": 0,
        }

    listings_qs = (
        Property.objects.filter(is_active=True, agent=agent)
        if agent
        else Property.objects.filter(is_active=True, posted_by=user)
    )
    total_views = sum(listings_qs.values_list("views_count", flat=True))

    return {
        "has_agent_profile": agent is not None,
        "agent_type": agent.agent_type if agent else None,
        "subscription": SubscriptionSerializer(subscription).data if subscription else None,
        "usage": usage,
        "packages_target": packages_target,
        "stats": {
            "total_listings": usage["listings_count"],
            "total_views": total_views,
            "vip_listings": usage["vip_listings_count"],
            "active_subscription": subscription is not None and subscription.is_valid,
        },
    }
