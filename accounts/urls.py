from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    AgentDetailView,
    AgentListView,
    AgentManageListView,
    CompanyManageDetailView,
    CompanyManageListCreateView,
    InviteCodeDetailView,
    InviteCodeListCreateView,
    InvitePreviewView,
    MembershipAcceptView,
    MembershipDenyView,
    MembershipRequestListView,
    MeView,
    RegisterView,
)
from .otp_views import OTPSendView, OTPVerifyView

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/login/", TokenObtainPairView.as_view(), name="auth-login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="auth-refresh"),
    path("auth/otp/send/", OTPSendView.as_view(), name="auth-otp-send"),
    path("auth/otp/verify/", OTPVerifyView.as_view(), name="auth-otp-verify"),
    path("auth/me/", MeView.as_view(), name="auth-me"),
    path("agents/", AgentListView.as_view(), name="agent-list"),
    path("agents/manage/", AgentManageListView.as_view(), name="agent-manage-list"),
    path(
        "agents/companies/manage/",
        CompanyManageListCreateView.as_view(),
        name="agent-companies-manage",
    ),
    path(
        "agents/companies/manage/<int:pk>/",
        CompanyManageDetailView.as_view(),
        name="agent-company-manage-detail",
    ),
    path("agents/invites/preview/", InvitePreviewView.as_view(), name="invite-preview"),
    path("agents/invites/", InviteCodeListCreateView.as_view(), name="invite-list-create"),
    path("agents/invites/<int:pk>/", InviteCodeDetailView.as_view(), name="invite-detail"),
    path(
        "agents/memberships/",
        MembershipRequestListView.as_view(),
        name="membership-requests",
    ),
    path(
        "agents/memberships/<int:pk>/accept/",
        MembershipAcceptView.as_view(),
        name="membership-accept",
    ),
    path(
        "agents/memberships/<int:pk>/deny/",
        MembershipDenyView.as_view(),
        name="membership-deny",
    ),
    path("agents/<int:pk>/", AgentDetailView.as_view(), name="agent-detail"),
]
