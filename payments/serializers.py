# payments/serializers.py
from decimal import Decimal
from rest_framework import serializers

from .models import PaymentTransaction, Refund, OrderCommission
from orders.models import Order, PaymentMethod, PaymentStatus


class PaymentTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentTransaction
        fields = [
            "id",
            "order",
            "amount",
            "currency",
            "method",
            "status",
            "provider_reference",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class RefundSerializer(serializers.ModelSerializer):
    class Meta:
        model = Refund
        fields = [
            "id",
            "order",
            "payment_transaction",
            "amount",
            "currency",
            "status",
            "reason",
            "provider_reference",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class OrderCommissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderCommission
        fields = [
            "order",
            "restaurant",
            "commission_rate",
            "food_subtotal",
            "commission_amount",
            "restaurant_net_amount",
            "created_at",
        ]
        read_only_fields = fields


class PayOrderSerializer(serializers.Serializer):
    """
    Request payload for paying an order.
    In practice, payment_method should match the order.payment_method,
    but we allow overriding here for flexibility.
    """
    payment_method = serializers.ChoiceField(choices=PaymentMethod.choices)
    # For MVP we always charge full order.total_amount
    # You could add `amount` here for partial payments if needed.


class RefundOrderSerializer(serializers.Serializer):
    """
    Request payload for refunding an order.
    MVP: full refund (amount = order.total_amount).
    """
    reason = serializers.CharField(required=False, allow_blank=True)

    # If you want partial refunds later:
    # amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
