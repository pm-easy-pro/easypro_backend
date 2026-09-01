from rest_framework import serializers

from .models import Location, LocationAlias


class LocationAliasSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocationAlias
        fields = ["id", "name"]


class LocationSerializer(serializers.ModelSerializer):
    aliases = LocationAliasSerializer(many=True, read_only=True)
    district_display = serializers.CharField(source="get_district_display", read_only=True)

    class Meta:
        model = Location
        fields = [
            "id",
            "district",
            "district_display",
            "official_address",
            "description",
            "latitude",
            "longitude",
            "aliases",
        ]
