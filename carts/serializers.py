# carts/serializers.py
from decimal import Decimal
from rest_framework import serializers

from .models import Cart, CartItem, DeliveryType
from menus.models import MenuItem


class CartItemSerializer(serializers.ModelSerializer):
    menu_item_id = serializers.IntegerField(source="menu_item.id", read_only=True)

    class Meta:
        model = CartItem
        fields = [
            "id",
            "menu_item_id",
            "item_name",
            "item_price",
            "item_image_url",
            "quantity",
            "line_total",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "menu_item_id",
            "item_name",
            "item_price",
            "item_image_url",
            "line_total",
            "created_at",
            "updated_at",
        ]


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    subtotal = serializers.SerializerMethodField()
    service_fee = serializers.SerializerMethodField()
    delivery_fee = serializers.SerializerMethodField()
    total = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = [
            "id",
            "restaurant",
            "delivery_type",
            "items",
            "subtotal",
            "service_fee",
            "delivery_fee",
            "total",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "restaurant",
            "subtotal",
            "service_fee",
            "delivery_fee",
            "total",
            "created_at",
            "updated_at",
            "items",
        ]

    def get_subtotal(self, obj) -> str:
        return str(obj.subtotal)

    def get_service_fee(self, obj) -> str:
        return str(obj.service_fee)

    def get_delivery_fee(self, obj) -> str:
        return str(obj.delivery_fee)

    def get_total(self, obj) -> str:
        return str(obj.total)


class CartDeliveryTypeUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = ["delivery_type"]


class AddOrUpdateCartItemSerializer(serializers.Serializer):
    menu_item_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)

    def validate_menu_item_id(self, value):
        try:
            menu_item = MenuItem.objects.get(id=value, is_active=True)
        except MenuItem.DoesNotExist:
            raise serializers.ValidationError("Menu item not found or inactive.")
        return value
