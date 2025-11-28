# restaurants/serializers.py
from rest_framework import serializers
from .models import Restaurant, RestaurantOpeningHour, RestaurantStatus
from accounts.models import UserRoles


class RestaurantOpeningHourSerializer(serializers.ModelSerializer):
    day_of_week_display = serializers.CharField(
        source="get_day_of_week_display", read_only=True
    )

    class Meta:
        model = RestaurantOpeningHour
        fields = [
            "id",
            "day_of_week",
            "day_of_week_display",
            "open_time",
            "close_time",
            "is_closed",
        ]
        read_only_fields = ["id", "day_of_week_display"]


class RestaurantSerializer(serializers.ModelSerializer):
    owner_id = serializers.IntegerField(source="owner.id", read_only=True)
    opening_hours = RestaurantOpeningHourSerializer(many=True, read_only=True)

    class Meta:
        model = Restaurant
        fields = [
            "id",
            "owner_id",
            "name",
            "licence_number",
            "phone_number",
            "email",
            "banner_image",
            "logo_image",
            "street",
            "city",
            "postal_code",
            "country",
            "latitude",
            "longitude",
            "status",
            "is_active",
            "created_at",
            "updated_at",
            "opening_hours",
        ]
        read_only_fields = [
            "id",
            "owner_id",
            "status",
            "created_at",
            "updated_at",
            "opening_hours",
        ]


class RestaurantCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restaurant
        fields = [
            "name",
            "licence_number",
            "phone_number",
            "email",
            "banner_image",
            "logo_image",
            "street",
            "city",
            "postal_code",
            "country",
            "latitude",
            "longitude",
            "is_active",
        ]

    def validate(self, attrs):
        # You can add extra licence validation/business rules here.
        return attrs
