# payments/models.py
from decimal import Decimal
from django.db import models
from django.utils import timezone

from orders.models import Order, PaymentStatus, PaymentMethod
from restaurants.models import Restaurant


class TransactionStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SUCCESS = "success", "Success"
    FAILED = "failed", "Failed"


class RefundStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SUCCESS = "success", "Success"
    FAILED = "failed", "Failed"


class PaymentTransaction(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="payment_transactions",
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default="EUR")

    method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
    )

    status = models.CharField(
        max_length=20,
        choices=TransactionStatus.choices,
        default=TransactionStatus.PENDING,
    )

    provider_reference = models.CharField(
        max_length=255,
        blank=True,
        help_text="Reference/transaction id from payment provider.",
    )
    raw_response = models.JSONField(
        null=True,
        blank=True,
        help_text="Optional raw response from provider for debugging.",
    )

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Payment Transaction"
        verbose_name_plural = "Payment Transactions"

    def __str__(self):
        return f"PaymentTransaction(order={self.order_id}, {self.amount} {self.currency}, {self.status})"


class Refund(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="refunds",
    )
    payment_transaction = models.ForeignKey(
        PaymentTransaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="refunds",
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default="EUR")

    status = models.CharField(
        max_length=20,
        choices=RefundStatus.choices,
        default=RefundStatus.PENDING,
    )
    reason = models.CharField(max_length=255, blank=True)

    provider_reference = models.CharField(
        max_length=255,
        blank=True,
        help_text="Refund reference from payment provider.",
    )
    raw_response = models.JSONField(
        null=True,
        blank=True,
        help_text="Optional raw response from provider.",
    )

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Refund"
        verbose_name_plural = "Refunds"

    def __str__(self):
        return f"Refund(order={self.order_id}, {self.amount} {self.currency}, {self.status})"


class OrderCommission(models.Model):
    """
    Stores commission for the platform and net payout for restaurant.
    Created when payment succeeds.
    """

    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name="commission",
    )
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name="commissions",
    )

    commission_rate = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        help_text="Commission % as decimal (e.g. 0.20 = 20%).",
    )

    food_subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2)
    restaurant_net_amount = models.DecimalField(max_digits=10, decimal_places=2)

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Order Commission"
        verbose_name_plural = "Order Commissions"

    def __str__(self):
        return f"OrderCommission(order={self.order_id}, rate={self.commission_rate}, commission={self.commission_amount})"
