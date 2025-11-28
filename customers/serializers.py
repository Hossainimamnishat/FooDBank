# customers/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import CustomerProfile, Address
from accounts.models import UserRoles

User = get_user_model()


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            "id",
            "label",
            "full_name",
            "phone_number",
            "street",
            "city",
            "postal_code",
            "country",
            "latitude",
            "longitude",
            "is_default",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        # You can put additional validation here if needed
        return attrs


class CustomerProfileSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_first_name = serializers.CharField(source="user.first_name", read_only=True)
    user_last_name = serializers.CharField(source="user.last_name", read_only=True)
    addresses = AddressSerializer(many=True, read_only=True)

    class Meta:
        model = CustomerProfile
        fields = [
            "id",
            "user_email",
            "user_first_name",
            "user_last_name",
            "created_at",
            "updated_at",
            "addresses",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "addresses"]
