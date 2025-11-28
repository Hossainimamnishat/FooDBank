# menus/serializers.py
from rest_framework import serializers
from .models import MenuCategory, MenuItem
from restaurants.models import Restaurant


class MenuCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuCategory
        fields = [
            "id",
            "restaurant",
            "name",
            "description",
            "sort_order",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "restaurant"]


class MenuItemSerializer(serializers.ModelSerializer):
    category = MenuCategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        source="category",
        queryset=MenuCategory.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = MenuItem
        fields = [
            "id",
            "restaurant",
            "category",
            "category_id",
            "name",
            "description",
            "ingredients",
            "price",
            "image_url",
            "quantity",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "restaurant", "category"]


class MenuItemCreateUpdateSerializer(serializers.ModelSerializer):
    category_id = serializers.PrimaryKeyRelatedField(
        source="category",
        queryset=MenuCategory.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = MenuItem
        fields = [
            "category_id",
            "name",
            "description",
            "ingredients",
            "price",
            "image_url",
            "quantity",
            "is_active",
        ]

    def validate(self, attrs):
        # You can add price / quantity validation here if needed
        return attrs
