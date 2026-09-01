from datetime import timedelta

from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Agent

from .models import Subscription, SubscriptionPackage
from .serializers import (
    SubscribeSerializer,
    SubscriptionPackageManageSerializer,
    SubscriptionPackageSerializer,
    SubscriptionSerializer,
    SubscriptionUsageSerializer,
    get_agent_for_user,
    get_dashboard_stats,
    get_subscription_usage,
)


class IsStaffUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_staff


class PackageListView(generics.ListAPIView):
    serializer_class = SubscriptionPackageSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None

    def get_queryset(self):
        qs = SubscriptionPackage.objects.filter(is_active=True)
        target = self.request.query_params.get("target_type")
        if target in (Agent.TYPE_INDIVIDUAL, Agent.TYPE_ORGANIZATION):
            qs = qs.filter(target_type=target)
        return qs


class PackageManageListCreateView(generics.ListCreateAPIView):
    serializer_class = SubscriptionPackageManageSerializer
    permission_classes = [IsStaffUser]
    pagination_class = None

    def get_queryset(self):
        return SubscriptionPackage.objects.all().order_by("sort_order", "price")


class PackageManageDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SubscriptionPackageManageSerializer
    permission_classes = [IsStaffUser]
    queryset = SubscriptionPackage.objects.all()

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=["is_active", "updated_at"])


class MySubscriptionView(APIView):
    def get(self, request):
        agent = get_agent_for_user(request.user)
        if not agent:
            return Response(
                {"detail": "Захиалга зөвхөн агент эсвэл байгууллагын профайлтай хэрэглэгчид боломжтой."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        subscription = Subscription.get_active_for_agent(agent)
        usage = get_subscription_usage(agent, subscription.package if subscription else None)

        return Response(
            {
                "subscription": SubscriptionSerializer(subscription).data if subscription else None,
                "usage": SubscriptionUsageSerializer(usage).data,
                "agent_type": agent.agent_type,
            }
        )


class SubscribeView(APIView):
    def post(self, request):
        agent = get_agent_for_user(request.user)
        if not agent:
            return Response(
                {"detail": "Захиалга зөвхөн агент эсвэл байгууллагын профайлтай хэрэглэгчид боломжтой."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = SubscribeSerializer(data=request.data, context={"agent": agent})
        serializer.is_valid(raise_exception=True)
        package = serializer.context["package"]

        existing = Subscription.get_active_for_agent(agent)
        if existing:
            existing.status = Subscription.STATUS_CANCELLED
            existing.cancelled_at = timezone.now()
            existing.auto_renew = False
            existing.save(update_fields=["status", "cancelled_at", "auto_renew", "updated_at"])

        now = timezone.now()
        subscription = Subscription.objects.create(
            agent=agent,
            package=package,
            status=Subscription.STATUS_ACTIVE,
            started_at=now,
            expires_at=now + timedelta(days=package.get_period_days()),
            auto_renew=True,
        )

        return Response(
            {
                "message": f"«{package.name}» багц амжилттай идэвхжлээ.",
                "subscription": SubscriptionSerializer(subscription).data,
            },
            status=status.HTTP_201_CREATED,
        )


class CancelSubscriptionView(APIView):
    def post(self, request):
        agent = get_agent_for_user(request.user)
        if not agent:
            return Response(
                {"detail": "Захиалга олдсонгүй."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        subscription = Subscription.get_active_for_agent(agent)
        if not subscription:
            return Response(
                {"detail": "Идэвхтэй захиалга байхгүй."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        subscription.status = Subscription.STATUS_CANCELLED
        subscription.cancelled_at = timezone.now()
        subscription.auto_renew = False
        subscription.save(update_fields=["status", "cancelled_at", "auto_renew", "updated_at"])

        return Response({"message": "Захиалга амжилттай цуцлагдлаа."})


class SubscriptionHistoryView(generics.ListAPIView):
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        agent = get_agent_for_user(self.request.user)
        if not agent:
            return Subscription.objects.none()
        return Subscription.objects.filter(agent=agent).select_related("package").order_by("-started_at")


class DashboardStatsView(APIView):
    def get(self, request):
        return Response(get_dashboard_stats(request.user))
