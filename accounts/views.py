import secrets
import string

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Agent, InviteCode
from .permissions import (
    IsStaffUser,
    can_manage_agents,
    get_company_admin_org,
    scoped_agents_queryset,
)
from .serializers import (
    AgentCompanyManageSerializer,
    AgentDetailSerializer,
    AgentSummarySerializer,
    InviteCodeCreateSerializer,
    InviteCodeSerializer,
    MembershipRequestSerializer,
    MeSerializer,
    ProfileUpdateSerializer,
    RegisterSerializer,
)

User = get_user_model()


def generate_unique_invite_code(organization: Agent) -> str:
    prefix = (organization.slug or "EP")[:4].upper().replace("-", "")
    alphabet = string.ascii_uppercase + string.digits
    for _ in range(20):
        body = "".join(secrets.choice(alphabet) for _ in range(6))
        code = f"{prefix}-{body}"
        if not InviteCode.objects.filter(code=code).exists():
            return code
    return f"{prefix}-{secrets.token_hex(4).upper()}"


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {"id": user.id, "username": user.username, "message": "Амжилттай бүртгэгдлээ"},
            status=status.HTTP_201_CREATED,
        )


class MeView(APIView):
    def get(self, request):
        user = User.objects.select_related("agent_profile__organization").get(pk=request.user.pk)
        return Response(MeSerializer(user).data)

    def patch(self, request):
        user = User.objects.select_related("agent_profile__organization").get(pk=request.user.pk)
        serializer = ProfileUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = serializer.update(user, serializer.validated_data)
        user = User.objects.select_related("agent_profile__organization").get(pk=user.pk)
        return Response(MeSerializer(user).data)


class AgentListView(generics.ListAPIView):
    serializer_class = AgentSummarySerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["agent_type", "organization", "is_verified", "membership_status"]
    search_fields = ["display_name", "company_name", "phone"]

    def get_queryset(self):
        qs = Agent.objects.filter(is_active=True).select_related("organization")
        # Public directory: only approved individuals + organizations
        include_pending = self.request.query_params.get("include_pending", "").lower() in (
            "true",
            "1",
            "yes",
        )
        if not include_pending:
            qs = qs.filter(
                Q(agent_type=Agent.TYPE_ORGANIZATION)
                | Q(membership_status=Agent.MEMBERSHIP_APPROVED)
            )
        return qs


class AgentDetailView(generics.RetrieveAPIView):
    serializer_class = AgentDetailSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return (
            Agent.objects.filter(is_active=True)
            .filter(
                Q(agent_type=Agent.TYPE_ORGANIZATION)
                | Q(membership_status=Agent.MEMBERSHIP_APPROVED)
            )
            .select_related("organization")
            .prefetch_related("member_agents")
        )


class AgentManageListView(generics.ListAPIView):
    """Staff: all agents. Company admin: only their company agents. Others: empty."""

    serializer_class = MembershipRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["display_name", "phone", "email", "title"]
    ordering = ["display_name"]

    def get_queryset(self):
        user = self.request.user
        if not can_manage_agents(user):
            return Agent.objects.none()
        qs = scoped_agents_queryset(user)
        status_filter = self.request.query_params.get("membership_status")
        if status_filter in {
            Agent.MEMBERSHIP_PENDING,
            Agent.MEMBERSHIP_APPROVED,
            Agent.MEMBERSHIP_DENIED,
        }:
            qs = qs.filter(membership_status=status_filter)
        return qs


class CompanyManageListCreateView(generics.ListCreateAPIView):
    serializer_class = AgentCompanyManageSerializer
    permission_classes = [IsStaffUser]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    pagination_class = None
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["company_name", "phone", "email", "address", "slug"]
    ordering_fields = ["company_name", "created_at", "is_verified", "is_active"]
    ordering = ["company_name"]

    def get_queryset(self):
        qs = Agent.objects.filter(agent_type=Agent.TYPE_ORGANIZATION).select_related(
            "user"
        ).prefetch_related("member_agents", "properties")
        status_filter = self.request.query_params.get("status")
        if status_filter == "active":
            qs = qs.filter(is_active=True)
        elif status_filter == "inactive":
            qs = qs.filter(is_active=False)
        verified = self.request.query_params.get("is_verified")
        if verified in ("true", "1", "yes"):
            qs = qs.filter(is_verified=True)
        elif verified in ("false", "0", "no"):
            qs = qs.filter(is_verified=False)
        return qs


class CompanyManageDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AgentCompanyManageSerializer
    permission_classes = [IsStaffUser]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        return Agent.objects.filter(agent_type=Agent.TYPE_ORGANIZATION).select_related(
            "user"
        ).prefetch_related("member_agents", "properties")

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=["is_active", "updated_at"])


class InvitePreviewView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        code = (request.query_params.get("code") or "").strip().upper()
        if not code:
            return Response(
                {"detail": "Урилгын код оруулна уу."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        invite = InviteCode.objects.select_related("organization").filter(code__iexact=code).first()
        if not invite:
            return Response(
                {
                    "code": code,
                    "organization_id": None,
                    "organization_name": None,
                    "is_valid": False,
                    "message": "Урилгын код олдсонгүй.",
                }
            )
        valid = invite.is_redeemable()
        return Response(
            {
                "code": invite.code,
                "organization_id": invite.organization_id,
                "organization_name": invite.organization.get_display_label(),
                "is_valid": valid,
                "message": "Хүчинтэй урилгын код." if valid else "Урилгын код хүчингүй эсвэл хугацаа дууссан.",
            }
        )


class InviteCodeListCreateView(generics.ListCreateAPIView):
    serializer_class = InviteCodeSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        user = self.request.user
        qs = InviteCode.objects.select_related("organization", "created_by")
        org = get_company_admin_org(user)
        if user.is_staff:
            org_id = self.request.query_params.get("organization")
            if org_id:
                qs = qs.filter(organization_id=org_id)
            elif org:
                qs = qs.filter(organization=org)
            return qs
        if org:
            return qs.filter(organization=org)
        return InviteCode.objects.none()

    def create(self, request, *args, **kwargs):
        user = request.user
        org_admin = get_company_admin_org(user)
        payload = InviteCodeCreateSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        data = payload.validated_data

        organization = data.get("organization")
        if user.is_staff and organization:
            pass
        elif org_admin:
            organization = org_admin
        else:
            return Response(
                {"detail": "Урилгын код үүсгэх эрх зөвхөн company admin эсвэл staff-д байна."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if organization.agent_type != Agent.TYPE_ORGANIZATION or not organization.is_active:
            return Response(
                {"detail": "Идэвхтэй компани сонгоно уу."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        invite = InviteCode.objects.create(
            organization=organization,
            code=generate_unique_invite_code(organization),
            created_by=user,
            max_uses=data.get("max_uses"),
            expires_at=data.get("expires_at"),
            note=data.get("note") or "",
        )
        return Response(
            InviteCodeSerializer(invite).data,
            status=status.HTTP_201_CREATED,
        )


class InviteCodeDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = InviteCodeSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "patch", "delete", "head", "options"]

    def get_queryset(self):
        user = self.request.user
        qs = InviteCode.objects.select_related("organization", "created_by")
        org = get_company_admin_org(user)
        if user.is_staff:
            return qs
        if org:
            return qs.filter(organization=org)
        return InviteCode.objects.none()

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=["is_active", "updated_at"])

    def partial_update(self, request, *args, **kwargs):
        invite = self.get_object()
        allowed = {}
        if "is_active" in request.data:
            allowed["is_active"] = request.data.get("is_active") in (True, "true", "True", "1", 1)
        if "note" in request.data:
            allowed["note"] = request.data.get("note") or ""
        if "max_uses" in request.data:
            raw = request.data.get("max_uses")
            allowed["max_uses"] = None if raw in ("", None) else int(raw)
        if "expires_at" in request.data:
            allowed["expires_at"] = request.data.get("expires_at") or None
        for key, value in allowed.items():
            setattr(invite, key, value)
        invite.save()
        return Response(InviteCodeSerializer(invite).data)


class MembershipRequestListView(generics.ListAPIView):
    """Company admin: list invite-based agent registrations for their org."""

    serializer_class = MembershipRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        user = self.request.user
        org = get_company_admin_org(user)
        status_filter = self.request.query_params.get("status") or Agent.MEMBERSHIP_PENDING

        qs = Agent.objects.filter(
            agent_type=Agent.TYPE_INDIVIDUAL,
            organization__isnull=False,
        ).select_related("organization", "user", "invited_via", "reviewed_by")

        if user.is_staff:
            org_id = self.request.query_params.get("organization")
            if org_id:
                qs = qs.filter(organization_id=org_id)
            elif org:
                qs = qs.filter(organization=org)
        elif org:
            qs = qs.filter(organization=org)
        else:
            return Agent.objects.none()

        if status_filter != "all":
            qs = qs.filter(membership_status=status_filter)
        return qs.order_by("-created_at")


class MembershipAcceptView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        agent = self._get_member(request, pk)
        if isinstance(agent, Response):
            return agent
        if agent.membership_status == Agent.MEMBERSHIP_APPROVED:
            return Response({"detail": "Аль хэдийн зөвшөөрөгдсөн."})
        agent.membership_status = Agent.MEMBERSHIP_APPROVED
        agent.is_verified = True
        agent.is_active = True
        agent.reviewed_at = timezone.now()
        agent.reviewed_by = request.user
        agent.save(
            update_fields=[
                "membership_status",
                "is_verified",
                "is_active",
                "reviewed_at",
                "reviewed_by",
                "updated_at",
            ]
        )
        return Response(
            {
                "message": "Агентыг зөвшөөрлөө.",
                "agent": MembershipRequestSerializer(agent, context={"request": request}).data,
            }
        )

    def _get_member(self, request, pk):
        user = request.user
        org = get_company_admin_org(user)
        try:
            agent = Agent.objects.select_related("organization", "user", "invited_via").get(
                pk=pk,
                agent_type=Agent.TYPE_INDIVIDUAL,
                organization__isnull=False,
            )
        except Agent.DoesNotExist:
            return Response({"detail": "Бүртгэл олдсонгүй."}, status=status.HTTP_404_NOT_FOUND)

        if user.is_staff:
            return agent
        if org and agent.organization_id == org.id:
            return agent
        return Response({"detail": "Зөвшөөрөлгүй."}, status=status.HTTP_403_FORBIDDEN)


class MembershipDenyView(MembershipAcceptView):
    def post(self, request, pk):
        agent = self._get_member(request, pk)
        if isinstance(agent, Response):
            return agent
        if agent.membership_status == Agent.MEMBERSHIP_DENIED:
            return Response({"detail": "Аль хэдийн татгалзсан."})
        agent.membership_status = Agent.MEMBERSHIP_DENIED
        agent.is_verified = False
        agent.is_active = False
        agent.reviewed_at = timezone.now()
        agent.reviewed_by = request.user
        agent.save(
            update_fields=[
                "membership_status",
                "is_verified",
                "is_active",
                "reviewed_at",
                "reviewed_by",
                "updated_at",
            ]
        )
        return Response(
            {
                "message": "Бүртгэлийг татгалзлаа.",
                "agent": MembershipRequestSerializer(agent, context={"request": request}).data,
            }
        )
