from django.db.models import Q
from django_filters import rest_framework as filters

from .models import Property


class PropertyFilter(filters.FilterSet):
    listing_type = filters.CharFilter(field_name="listing_type")
    district = filters.CharFilter(field_name="district")
    property_type = filters.CharFilter(field_name="property_type")
    condition = filters.CharFilter(field_name="condition")
    room_count = filters.NumberFilter(field_name="room_count")
    room_count_min = filters.NumberFilter(field_name="room_count", lookup_expr="gte")
    price_min = filters.NumberFilter(field_name="price", lookup_expr="gte")
    price_max = filters.NumberFilter(field_name="price", lookup_expr="lte")
    area_min = filters.NumberFilter(field_name="area_m2", lookup_expr="gte")
    area_max = filters.NumberFilter(field_name="area_m2", lookup_expr="lte")
    location = filters.CharFilter(method="filter_location")
    locations = filters.CharFilter(method="filter_locations")
    search = filters.CharFilter(method="filter_search")
    payment_terms = filters.CharFilter(method="filter_payment_terms")
    is_verified = filters.BooleanFilter(field_name="is_verified")
    is_vip = filters.BooleanFilter(field_name="is_vip")
    agent = filters.NumberFilter(field_name="agent_id")
    posted_by = filters.NumberFilter(field_name="posted_by_id")
    mine = filters.BooleanFilter(method="filter_mine")
    exclude_property_type = filters.CharFilter(method="filter_exclude_property_type")

    class Meta:
        model = Property
        fields = [
            "listing_type",
            "district",
            "property_type",
            "condition",
            "room_count",
        ]

    def filter_location(self, queryset, name, value):
        return self._filter_by_location_terms(queryset, [value])

    def filter_locations(self, queryset, name, value):
        terms = [t.strip() for t in value.split(",") if t.strip()]
        return self._filter_by_location_terms(queryset, terms)

    def _filter_by_location_terms(self, queryset, terms):
        if not terms:
            return queryset
        q = Q()
        for term in terms:
            q |= (
                Q(official_address__icontains=term)
                | Q(unofficial_addresses__icontains=term)
                | Q(district__icontains=term)
                | Q(location__official_address__icontains=term)
                | Q(location__aliases__name__icontains=term)
            )
        return queryset.filter(q).distinct()

    def filter_payment_terms(self, queryset, name, value):
        terms = [t.strip() for t in value.split(",") if t.strip()]
        if not terms:
            return queryset
        q = Q()
        for term in terms:
            q |= Q(payment_terms__contains=[term])
        return queryset.filter(q).distinct()

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            Q(title__icontains=value)
            | Q(description__icontains=value)
            | Q(official_address__icontains=value)
            | Q(unofficial_addresses__icontains=value)
            | Q(district__icontains=value)
            | Q(location__aliases__name__icontains=value)
        ).distinct()

    def filter_mine(self, queryset, name, value):
        if not value:
            return queryset
        request = getattr(self, "request", None)
        if not request or not request.user.is_authenticated:
            return queryset.none()
        from accounts.permissions import scoped_properties_queryset

        allowed_ids = scoped_properties_queryset(request.user).values_list("pk", flat=True)
        return queryset.filter(pk__in=allowed_ids)

    def filter_exclude_property_type(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.exclude(property_type=value)


ORDERING_MAP = {
    "newest": "-created_at",
    "oldest": "created_at",
    "price_asc": "price",
    "price_desc": "-price",
    "area_desc": "-area_m2",
    "most_viewed": "-views_count",
}
