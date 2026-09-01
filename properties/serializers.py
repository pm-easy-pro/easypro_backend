from rest_framework import serializers

from accounts.models import Agent
from accounts.serializers import AgentSummarySerializer, PropertyAgentSerializer, UserSerializer
from locations.serializers import LocationSerializer

from .models import Property


class PropertyListSerializer(serializers.ModelSerializer):
    listing_type_display = serializers.CharField(source="get_listing_type_display", read_only=True)
    property_type_display = serializers.CharField(source="get_property_type_display", read_only=True)
    condition_display = serializers.CharField(source="get_condition_display", read_only=True)
    view_direction_display = serializers.CharField(
        source="get_view_direction_display", read_only=True
    )
    listing_owner_display = serializers.CharField(
        source="get_listing_owner_type_display", read_only=True
    )
    land_right_type_display = serializers.CharField(
        source="get_land_right_type_display", read_only=True
    )
    land_use_type_display = serializers.CharField(
        source="get_land_use_type_display", read_only=True
    )
    thumbnail_url = serializers.SerializerMethodField()
    location_detail = LocationSerializer(source="location", read_only=True)
    agent_detail = PropertyAgentSerializer(source="agent", read_only=True)

    class Meta:
        model = Property
        fields = [
            "id",
            "title",
            "listing_type",
            "listing_type_display",
            "property_type",
            "property_type_display",
            "condition",
            "condition_display",
            "listing_owner_type",
            "listing_owner_display",
            "agent",
            "agent_detail",
            "district",
            "official_address",
            "unofficial_addresses",
            "location",
            "location_detail",
            "price",
            "area_m2",
            "room_count",
            "floor",
            "total_floor",
            "has_elevator",
            "window_count",
            "bathroom_count",
            "view_direction",
            "view_direction_display",
            "garage",
            "building_type",
            "balcony",
            "furnished",
            "payment_terms",
            "year_built",
            "parcel_number",
            "land_right_type",
            "land_right_type_display",
            "land_contract_start",
            "land_contract_end",
            "land_use_type",
            "land_use_type_display",
            "latitude",
            "longitude",
            "is_verified",
            "is_vip",
            "views_count",
            "status",
            "thumbnail_url",
            "images",
            "created_at",
        ]

    def get_thumbnail_url(self, obj):
        request = self.context.get("request")
        if obj.thumbnail:
            url = obj.thumbnail.url
            if request:
                return request.build_absolute_uri(url)
            return url
        if obj.images:
            return obj.images[0]
        return None


class PropertyDetailSerializer(PropertyListSerializer):
    description = serializers.CharField()
    posted_by_detail = UserSerializer(source="posted_by", read_only=True)
    related_properties = serializers.SerializerMethodField()

    class Meta(PropertyListSerializer.Meta):
        fields = PropertyListSerializer.Meta.fields + [
            "description",
            "updated_at",
            "posted_by",
            "posted_by_detail",
            "related_properties",
        ]

    def get_related_properties(self, obj):
        related_qs = self.context.get("related_properties")
        if related_qs is None:
            return []
        return PropertyListSerializer(
            related_qs, many=True, context=self.context
        ).data


class PropertyCreateSerializer(serializers.ModelSerializer):
    unofficial_addresses = serializers.JSONField(required=False)
    images = serializers.JSONField(required=False)
    floor = serializers.IntegerField(required=False, allow_null=True)
    total_floor = serializers.IntegerField(required=False, allow_null=True)
    window_count = serializers.IntegerField(required=False, allow_null=True)
    bathroom_count = serializers.IntegerField(required=False, allow_null=True)
    year_built = serializers.IntegerField(required=False, allow_null=True)
    room_count = serializers.IntegerField(required=False, allow_null=True, min_value=1)

    class Meta:
        model = Property
        fields = [
            "id",
            "title",
            "description",
            "listing_type",
            "property_type",
            "building_type",
            "condition",
            "district",
            "official_address",
            "unofficial_addresses",
            "location",
            "price",
            "area_m2",
            "room_count",
            "floor",
            "total_floor",
            "has_elevator",
            "window_count",
            "bathroom_count",
            "view_direction",
            "garage",
            "balcony",
            "furnished",
            "payment_terms",
            "year_built",
            "parcel_number",
            "land_right_type",
            "land_contract_start",
            "land_contract_end",
            "land_use_type",
            "latitude",
            "longitude",
            "thumbnail",
            "images",
            "listing_owner_type",
            "agent",
        ]
        read_only_fields = ["id"]

    OPTIONAL_EMPTY_TO_NULL = (
        "floor",
        "total_floor",
        "window_count",
        "bathroom_count",
        "year_built",
        "room_count",
        "location",
        "agent",
        "land_contract_start",
        "land_contract_end",
    )

    def to_internal_value(self, data):
        if hasattr(data, "copy"):
            data = data.copy()
        else:
            data = dict(data)
        for field in self.OPTIONAL_EMPTY_TO_NULL:
            if data.get(field) == "":
                data[field] = None
        return super().to_internal_value(data)

    def validate_room_count(self, value):
        if value is None:
            return 1
        return value

    def validate_unofficial_addresses(self, value):
        if isinstance(value, str):
            import json

            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return [a.strip() for a in value.split(",") if a.strip()]
        return value or []

    def validate_images(self, value):
        if isinstance(value, str):
            import json

            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return [u.strip() for u in value.split(",") if u.strip()]
        return value or []

    def validate(self, attrs):
        owner_type = attrs.get("listing_owner_type", Property.LISTING_OWNER_OWNER)
        agent = attrs.get("agent")
        request = self.context.get("request")
        user = getattr(request, "user", None) if request else None
        profile = getattr(user, "agent_profile", None) if user else None

        if owner_type == Property.LISTING_OWNER_OWNER:
            if agent:
                raise serializers.ValidationError(
                    {"agent": "Эзэн өөрөө зар нэмэхэд агент сонгох шаардлагагүй."}
                )
            attrs["agent"] = None
        elif owner_type == Property.LISTING_OWNER_AGENT:
            if not agent:
                if profile and profile.agent_type == Agent.TYPE_INDIVIDUAL:
                    attrs["agent"] = profile
                    agent = profile
                else:
                    raise serializers.ValidationError(
                        {"agent": "Агент профайл шаардлагатай. Агентээр бүртгүүлнэ үү."}
                    )
            elif agent.agent_type != Agent.TYPE_INDIVIDUAL:
                raise serializers.ValidationError({"agent": "Зөвхөн хувь хүний агент сонгоно уу."})
            agent = attrs.get("agent")
            if agent and agent.membership_status != Agent.MEMBERSHIP_APPROVED:
                raise serializers.ValidationError(
                    {
                        "listing_owner_type": (
                            "Агент бүртгэл company admin-ийн зөвшөөрлийг хүлээж байна. "
                            "Зөвшөөрөгдсөний дараа зар нэмнэ үү."
                        )
                    }
                )
        elif owner_type == Property.LISTING_OWNER_COMPANY:
            if not agent:
                if profile and profile.agent_type == Agent.TYPE_ORGANIZATION:
                    attrs["agent"] = profile
                else:
                    raise serializers.ValidationError(
                        {"agent": "Компанийн профайл шаардлагатай. Компаниар бүртгүүлнэ үү."}
                    )
            elif agent.agent_type != Agent.TYPE_ORGANIZATION:
                raise serializers.ValidationError({"agent": "Зөвхөн байгууллага сонгоно уу."})

        property_type = attrs.get(
            "property_type",
            getattr(self.instance, "property_type", None) if self.instance else None,
        )
        if property_type == Property.PROPERTY_LAND:
            if not attrs.get("parcel_number") and not (self.instance and self.instance.parcel_number):
                raise serializers.ValidationError(
                    {"parcel_number": "Нэгж талбарын дугаар оруулна уу."}
                )
            land_right = attrs.get(
                "land_right_type",
                getattr(self.instance, "land_right_type", "") if self.instance else "",
            )
            if not land_right:
                raise serializers.ValidationError(
                    {"land_right_type": "Эрхийн төрөл сонгоно уу."}
                )
            if not attrs.get("land_use_type") and not (
                self.instance and self.instance.land_use_type
            ):
                raise serializers.ValidationError(
                    {"land_use_type": "Газар ашиглалтын төрөл сонгоно уу."}
                )
            if land_right in (Property.LAND_RIGHT_POSSESSION, Property.LAND_RIGHT_USE):
                start = attrs.get("land_contract_start")
                end = attrs.get("land_contract_end")
                if self.instance:
                    if start is None:
                        start = self.instance.land_contract_start
                    if end is None:
                        end = self.instance.land_contract_end
                if not start or not end:
                    raise serializers.ValidationError(
                        {
                            "land_contract_start": (
                                "Эзэмших/Ашиглах эрхийн гэрээний огноо оруулна уу."
                            )
                        }
                    )
                if start and end and start > end:
                    raise serializers.ValidationError(
                        {"land_contract_end": "Дуусах огноо эхлэх огнооноос хойш байх ёстой."}
                    )
            else:
                attrs["land_contract_start"] = None
                attrs["land_contract_end"] = None

        return attrs

    def create(self, validated_data):
        validated_data.setdefault("status", "active")
        validated_data.setdefault("is_active", True)
        validated_data.setdefault("room_count", 1)
        # ImageField cannot accept remote URLs from JSON create
        validated_data.pop("thumbnail", None)
        return super().create(validated_data)


class PropertyManageSerializer(serializers.ModelSerializer):
    listing_type_display = serializers.CharField(source="get_listing_type_display", read_only=True)
    property_type_display = serializers.CharField(source="get_property_type_display", read_only=True)
    condition_display = serializers.CharField(source="get_condition_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    listing_owner_display = serializers.CharField(
        source="get_listing_owner_type_display", read_only=True
    )
    land_right_type_display = serializers.CharField(
        source="get_land_right_type_display", read_only=True
    )
    land_use_type_display = serializers.CharField(
        source="get_land_use_type_display", read_only=True
    )
    thumbnail_url = serializers.SerializerMethodField()
    agent_detail = AgentSummarySerializer(source="agent", read_only=True)
    posted_by_detail = UserSerializer(source="posted_by", read_only=True)
    unofficial_addresses = serializers.JSONField(required=False)
    images = serializers.JSONField(required=False)
    payment_terms = serializers.JSONField(required=False)

    class Meta:
        model = Property
        fields = [
            "id",
            "title",
            "description",
            "listing_type",
            "listing_type_display",
            "property_type",
            "property_type_display",
            "building_type",
            "condition",
            "condition_display",
            "district",
            "official_address",
            "unofficial_addresses",
            "location",
            "price",
            "area_m2",
            "room_count",
            "floor",
            "total_floor",
            "has_elevator",
            "window_count",
            "bathroom_count",
            "view_direction",
            "garage",
            "balcony",
            "furnished",
            "payment_terms",
            "year_built",
            "parcel_number",
            "land_right_type",
            "land_right_type_display",
            "land_contract_start",
            "land_contract_end",
            "land_use_type",
            "land_use_type_display",
            "latitude",
            "longitude",
            "is_verified",
            "is_vip",
            "views_count",
            "status",
            "status_display",
            "thumbnail",
            "thumbnail_url",
            "images",
            "listing_owner_type",
            "listing_owner_display",
            "agent",
            "agent_detail",
            "posted_by",
            "posted_by_detail",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["views_count", "created_at", "updated_at"]

    OPTIONAL_EMPTY_TO_NULL = (
        "floor",
        "total_floor",
        "window_count",
        "bathroom_count",
        "year_built",
        "latitude",
        "longitude",
        "location",
        "agent",
        "land_contract_start",
        "land_contract_end",
    )

    def to_internal_value(self, data):
        if hasattr(data, "copy"):
            data = data.copy()
        else:
            data = dict(data)
        for field in self.OPTIONAL_EMPTY_TO_NULL:
            if data.get(field) == "":
                data[field] = None
        return super().to_internal_value(data)

    def get_thumbnail_url(self, obj):
        request = self.context.get("request")
        if obj.thumbnail:
            url = obj.thumbnail.url
            return request.build_absolute_uri(url) if request else url
        if obj.images:
            return obj.images[0]
        return None

    def validate_unofficial_addresses(self, value):
        if isinstance(value, str):
            import json

            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return [a.strip() for a in value.split(",") if a.strip()]
        return value or []

    def validate_images(self, value):
        if isinstance(value, str):
            import json

            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return [u.strip() for u in value.split(",") if u.strip()]
        return value or []

    def create(self, validated_data):
        validated_data.setdefault("status", "active")
        validated_data.setdefault("is_active", True)
        return super().create(validated_data)
