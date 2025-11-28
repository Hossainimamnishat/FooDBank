# orders/models.py
from decimal import Decimal

from django.db import models
from django.utils import timezone

from customers.models import CustomerProfile, Address
from restaurants.models import Restaurant
from carts.models import DeliveryType
from menus.models import MenuItem


class OrderStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    ACCEPTED = "accepted", "Accepted by restaurant"
    PREPARING = "preparing", "Preparing"
    READY_FOR_PICKUP = "ready_for_pickup", "Ready for pickup"
    DRIVER_ASSIGNED = "driver_assigned", "Driver assigned"
    ON_THE_WAY = "on_the_way", "On the way"
    DELIVERED = "delivered", "Delivered"
    CANCELLED = "cancelled", "Cancelled"
    REFUNDED = "refunded", "Refunded"


class PaymentMethod(models.TextChoices):
    PAYPAL = "paypal", "PayPal"
    MASTERCARD = "mastercard", "MasterCard"
    BANK = "bank", "Bank"


class PaymentStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PAID = "paid", "Paid"
    FAILED = "failed", "Failed"
    REFUNDED = "refunded", "Refunded"


class Order(models.Model):
    customer = models.ForeignKey(
        CustomerProfile,
        on_delete=models.CASCADE,
        related_name="orders",
    )
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name="orders",
    )

    # Optional link to driver: will be defined later in delivery app
    driver = models.ForeignKey(
        "delivery.DriverProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )

    delivery_type = models.CharField(
        max_length=20,
        choices=DeliveryType.choices,
        default=DeliveryType.DELIVERY,
    )

    # Snapshot of delivery address & contact at order time
    address_full_name = models.CharField(max_length=255, blank=True)
    address_phone_number = models.CharField(max_length=20, blank=True)
    address_street = models.CharField(max_length=255, blank=True)
    address_city = models.CharField(max_length=100, blank=True)
    address_postal_code = models.CharField(max_length=20, blank=True)
    address_country = models.CharField(max_length=100, blank=True)
    address_latitude = models.FloatField(null=True, blank=True)
    address_longitude = models.FloatField(null=True, blank=True)

    delivery_note = models.TextField(blank=True)

    # Pricing
    food_subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    service_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tip_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default="EUR")

    # Payment
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
    )
    payment_reference = models.CharField(
        max_length=255,
        blank=True,
        help_text="External payment provider reference/transaction id",
    )

    status = models.CharField(
        max_length=30,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING,
    )

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.id} - {self.customer.user.email} - {self.restaurant.name}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
    )
    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_items",
        help_text="Original menu item, may be null if deleted later",
    )

    # Snapshot data
    item_name = models.CharField(max_length=255)
    item_description = models.TextField(blank=True)
    item_ingredients = models.TextField(blank=True)
    item_price = models.DecimalField(max_digits=8, decimal_places=2)
    item_image_url = models.URLField(max_length=500, null=True, blank=True)
    quantity = models.PositiveIntegerField()
    line_total = models.DecimalField(max_digits=10, decimal_places=2)

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"

    def __str__(self):
        return f"{self.item_name} x {self.quantity} (Order #{self.order_id})"
