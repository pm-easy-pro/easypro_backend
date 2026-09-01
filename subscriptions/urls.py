from django.urls import path

from .views import (
    CancelSubscriptionView,
    DashboardStatsView,
    MySubscriptionView,
    PackageListView,
    PackageManageDetailView,
    PackageManageListCreateView,
    SubscribeView,
    SubscriptionHistoryView,
)

urlpatterns = [
    path("subscriptions/packages/", PackageListView.as_view(), name="subscription-packages"),
    path("subscriptions/packages/manage/", PackageManageListCreateView.as_view(), name="subscription-packages-manage"),
    path("subscriptions/packages/manage/<int:pk>/", PackageManageDetailView.as_view(), name="subscription-package-manage-detail"),
    path("subscriptions/me/", MySubscriptionView.as_view(), name="subscription-me"),
    path("subscriptions/subscribe/", SubscribeView.as_view(), name="subscription-subscribe"),
    path("subscriptions/cancel/", CancelSubscriptionView.as_view(), name="subscription-cancel"),
    path("subscriptions/history/", SubscriptionHistoryView.as_view(), name="subscription-history"),
    path("subscriptions/dashboard/", DashboardStatsView.as_view(), name="subscription-dashboard"),
]
