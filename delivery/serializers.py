# delivery/serializers.py
from rest_framework import serializers
from decimal import Decimal

from .models import DriverProfile, DriverShift, DeliveryAssignment, VehicleType


class DriverProfileSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = DriverProfile
        fields = [
            "id",
            "user_email",
            "vehicle_type",
            "is_active",
            "hourly_rate",
            "per_km_rate",
            "service_area_city",
            "service_radius_km",
            "home_latitude",
            "home_longitude",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user_email", "created_at", "updated_at"]


class DriverProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverProfile
        fields = [
            "vehicle_type",
            "is_active",
            "service_area_city",
            "service_radius_km",
            "home_latitude",
            "home_longitude",
        ]


class DriverShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverShift
        fields = [
            "id",
            "driver",
            "start_time",
            "end_time",
            "total_minutes",
            "created_at",
            "is_open",
        ]
        read_only_fields = [
            "id",
            "driver",
            "start_time",
            "end_time",
            "total_minutes",
            "created_at",
            "is_open",
        ]


class DeliveryAssignmentSerializer(serializers.ModelSerializer):
    order_id = serializers.IntegerField(source="order.id", read_only=True)
    driver_id = serializers.IntegerField(source="driver.id", read_only=True)

    class Meta:
        model = DeliveryAssignment
        fields = [
            "id",
            "order_id",
            "driver_id",
            "distance_km",
            "per_km_rate",
            "distance_pay",
            "bonus_amount",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "order_id",
            "driver_id",
            "distance_km",
            "per_km_rate",
            "distance_pay",
            "bonus_amount",
            "created_at",
        ]
