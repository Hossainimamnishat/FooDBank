# orders/serializers.py
from rest_framework import serializers
from decimal import Decimal

from .models import Order, OrderItem, OrderStatus, PaymentMethod
from carts.models import DeliveryType
from customers.models import Address
from restaurants.models import Restaurant


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = [
            "id",
            "item_name",
            "item_description",
            "item_ingredients",
            "item_price",
            "item_image_url",
            "quantity",
            "line_total",
        ]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "customer",
            "restaurant",
            "driver",
            "delivery_type",
            "address_full_name",
            "address_phone_number",
            "address_street",
            "address_city",
            "address_postal_code",
            "address_country",
            "address_latitude",
            "address_longitude",
            "delivery_note",
            "food_subtotal",
            "service_fee",
            "delivery_fee",
            "tip_amount",
            "total_amount",
            "currency",
            "payment_method",
            "payment_status",
            "payment_reference",
            "status",
            "items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "customer",
            "restaurant",
            "driver",
            "food_subtotal",
            "service_fee",
            "delivery_fee",
            "total_amount",
            "currency",
            "payment_status",
            "payment_reference",
            "status",
            "items",
            "created_at",
            "updated_at",
        ]


class OrderCreateSerializer(serializers.Serializer):
    """
    Payload for creating an order from the current cart.
    """
    address_id = serializers.IntegerField(required=False, allow_null=True)
    delivery_type = serializers.ChoiceField(choices=DeliveryType.choices)
    delivery_note = serializers.CharField(required=False, allow_blank=True)
    tip_amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        min_value=Decimal("0.00"),
        default=Decimal("0.00"),
    )
    payment_method = serializers.ChoiceField(choices=PaymentMethod.choices)

    def validate(self, attrs):
        delivery_type = attrs.get("delivery_type")
        address_id = attrs.get("address_id")

        if delivery_type == DeliveryType.DELIVERY and not address_id:
            raise serializers.ValidationError(
                "address_id is required for delivery orders."
            )

        return attrs
# orders/serializers.py  (add these below existing imports & serializers)
from .models import OrderStatus


class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["status"]

    def validate_status(self, value):
        # Optional: restrict to “normal” flow statuses
        allowed = {
            OrderStatus.PENDING,
            OrderStatus.ACCEPTED,
            OrderStatus.PREPARING,
            OrderStatus.READY_FOR_PICKUP,
            OrderStatus.DRIVER_ASSIGNED,
            OrderStatus.ON_THE_WAY,
            OrderStatus.DELIVERED,
            OrderStatus.CANCELLED,
        }
        if value not in allowed:
            raise serializers.ValidationError("Invalid status value.")
        return value
