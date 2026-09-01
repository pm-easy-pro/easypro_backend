from django.db.models import F
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Agent
from accounts.permissions import (
    IsAuthenticatedManageUser,
    get_company_admin_org,
    scoped_properties_queryset,
    user_can_manage_property,
)
from locations.models import Location

from .filters import ORDERING_MAP, PropertyFilter
from .models import Property
from .serializers import (
    PropertyCreateSerializer,
    PropertyDetailSerializer,
    PropertyListSerializer,
    PropertyManageSerializer,
)
from .uploads import save_uploaded_images


def get_related_properties(property_obj, limit=8):
    qs = Property.objects.filter(
        is_active=True,
        status="active",
        property_type=property_obj.property_type,
    ).exclude(pk=property_obj.pk)
    if property_obj.location_id:
        qs = qs.filter(location_id=property_obj.location_id)
    else:
        qs = qs.filter(official_address=property_obj.official_address)
    return qs.select_related("location", "agent", "agent__organization")[:limit]


class PropertyListCreateView(generics.ListCreateAPIView):
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = PropertyFilter
    search_fields = ["title", "description", "official_address", "district"]

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        mine = self.request.query_params.get("mine", "").lower() in ("true", "1", "yes")
        if mine:
            qs = Property.objects.filter(is_active=True).select_related(
                "location", "agent", "agent__organization", "posted_by"
            )
        else:
            qs = (
                Property.objects.filter(is_active=True, status="active")
                .select_related("location", "agent", "agent__organization", "posted_by")
            )
        ordering = self.request.query_params.get("ordering")
        order_field = ORDERING_MAP.get(ordering, "-created_at") if ordering else "-created_at"
        return qs.order_by("-is_vip", order_field)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return PropertyCreateSerializer
        return PropertyListSerializer

    def perform_create(self, serializer):
        user = self.request.user
        listing_owner_type = serializer.validated_data.get(
            "listing_owner_type", Property.LISTING_OWNER_OWNER
        )
        agent = serializer.validated_data.get("agent")

        if listing_owner_type == Property.LISTING_OWNER_OWNER:
            agent = None
        elif listing_owner_type == Property.LISTING_OWNER_AGENT:
            profile = getattr(user, "agent_profile", None)
            if profile and profile.agent_type == Agent.TYPE_INDIVIDUAL:
                agent = profile
        elif listing_owner_type == Property.LISTING_OWNER_COMPANY:
            profile = getattr(user, "agent_profile", None)
            if profile and profile.agent_type == Agent.TYPE_ORGANIZATION:
                agent = profile

        serializer.save(posted_by=user, agent=agent)


class PropertyDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = PropertyDetailSerializer

    def get_queryset(self):
        return Property.objects.filter(is_active=True).select_related(
            "location", "agent", "agent__organization", "posted_by"
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        Property.objects.filter(pk=instance.pk).update(views_count=F("views_count") + 1)
        instance.refresh_from_db()

        related = list(get_related_properties(instance))
        serializer = self.get_serializer(
            instance,
            context={
                "request": request,
                "related_properties": related,
            },
        )
        return Response(serializer.data)


class PropertyManageListCreateView(generics.ListCreateAPIView):
    serializer_class = PropertyManageSerializer
    permission_classes = [IsAuthenticatedManageUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["listing_type", "property_type", "status", "is_vip", "is_verified", "district"]
    search_fields = ["title", "official_address", "district", "description"]

    def get_queryset(self):
        return scoped_properties_queryset(self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        user = self.request.user
        agent = serializer.validated_data.get("agent")
        owner_type = serializer.validated_data.get(
            "listing_owner_type", Property.LISTING_OWNER_OWNER
        )
        org = get_company_admin_org(user)
        profile = getattr(user, "agent_profile", None)

        if user.is_staff:
            serializer.save(posted_by=user)
            return

        if org:
            if owner_type == Property.LISTING_OWNER_COMPANY or not agent:
                agent = org
                owner_type = Property.LISTING_OWNER_COMPANY
            elif agent and agent.organization_id != org.id and agent.id != org.id:
                agent = org
                owner_type = Property.LISTING_OWNER_COMPANY
            serializer.save(
                posted_by=user,
                agent=agent,
                listing_owner_type=owner_type,
                is_verified=False,
            )
            return

        if profile and profile.agent_type == Agent.TYPE_INDIVIDUAL:
            serializer.save(
                posted_by=user,
                agent=profile,
                listing_owner_type=Property.LISTING_OWNER_AGENT,
                is_verified=False,
            )
            return

        serializer.save(
            posted_by=user,
            agent=None,
            listing_owner_type=Property.LISTING_OWNER_OWNER,
            is_verified=False,
        )


class PropertyManageDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PropertyManageSerializer
    permission_classes = [IsAuthenticatedManageUser]

    def get_queryset(self):
        return scoped_properties_queryset(self.request.user)

    def perform_update(self, serializer):
        user = self.request.user
        if user.is_staff:
            serializer.save()
            return

        serializer.validated_data.pop("is_verified", None)
        if not get_company_admin_org(user):
            serializer.validated_data.pop("is_vip", None)

        agent = serializer.validated_data.get("agent", serializer.instance.agent)
        org = get_company_admin_org(user)
        if org:
            if agent and agent.id != org.id and getattr(agent, "organization_id", None) != org.id:
                serializer.validated_data.pop("agent", None)
        else:
            serializer.validated_data.pop("agent", None)
            serializer.validated_data.pop("listing_owner_type", None)

        serializer.save()

    def perform_destroy(self, instance):
        if not user_can_manage_property(self.request.user, instance):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Энэ зарыг удирдах эрхгүй.")
        instance.is_active = False
        instance.status = "archived"
        instance.save(update_fields=["is_active", "status", "updated_at"])


class LocationListView(generics.ListAPIView):
    from locations.serializers import LocationSerializer

    serializer_class = LocationSerializer
    queryset = Location.objects.filter(is_active=True).prefetch_related("aliases")
    filter_backends = [filters.SearchFilter]
    search_fields = ["official_address", "aliases__name", "district"]


class FilterOptionsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        districts = (
            Property.objects.filter(is_active=True, status="active")
            .values_list("district", flat=True)
            .distinct()
            .order_by("district")
        )
        locations = Location.objects.filter(is_active=True).prefetch_related("aliases")
        from locations.serializers import LocationSerializer

        return Response(
            {
                "listing_types": [
                    {"value": c[0], "label": c[1]} for c in Property.LISTING_CHOICES
                ],
                "property_types": [
                    {"value": c[0], "label": c[1]} for c in Property.PROPERTY_CHOICES
                ],
                "real_estate_types": [
                    {"value": c[0], "label": c[1]}
                    for c in Property.PROPERTY_CHOICES
                    if c[0] != Property.PROPERTY_LAND
                ],
                "land_types": [
                    {"value": c[0], "label": c[1]}
                    for c in Property.PROPERTY_CHOICES
                    if c[0] == Property.PROPERTY_LAND
                ],
                "conditions": [
                    {"value": c[0], "label": c[1]} for c in Property.CONDITION_CHOICES
                ],
                "view_directions": [
                    {"value": c[0], "label": c[1]}
                    for c in Property.VIEW_DIRECTION_CHOICES
                    if c[0]
                ],
                "listing_owner_types": [
                    {"value": c[0], "label": c[1]} for c in Property.LISTING_OWNER_CHOICES
                ],
                "districts": [
                    {"value": d, "label": d.replace("_", " ").title()} for d in districts if d
                ],
                "district_choices": [
                    {"value": c[0], "label": c[1]} for c in Location.DISTRICT_CHOICES
                ],
                "payment_terms": [
                    {"value": c[0], "label": c[1]} for c in Property.PAYMENT_TERM_CHOICES
                ],
                "ordering": [
                    {"value": "newest", "label": "Шинээр нэмэгдсэн"},
                    {"value": "oldest", "label": "Хуучин"},
                    {"value": "price_asc", "label": "Үнэ өсөх"},
                    {"value": "price_desc", "label": "Үнэ буурах"},
                    {"value": "area_desc", "label": "Талбай их"},
                    {"value": "most_viewed", "label": "Их үзсэн"},
                ],
                "locations": LocationSerializer(locations, many=True).data,
            }
        )


class PropertyImageUploadView(APIView):
    """Upload one or more property images; returns public media URLs."""

    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        files = request.FILES.getlist("files")
        if not files and request.FILES.get("file"):
            files = [request.FILES["file"]]
        if not files:
            return Response(
                {"detail": "Зураг сонгоно уу (files)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            urls = save_uploaded_images(files, request=request)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"urls": urls}, status=status.HTTP_201_CREATED)
