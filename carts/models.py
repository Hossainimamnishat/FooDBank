# carts/models.py
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from customers.models import CustomerProfile
from restaurants.models import Restaurant
from menus.models import MenuItem


class DeliveryType(models.TextChoices):
    PICKUP = "pickup", "Pickup"
    DELIVERY = "delivery", "Delivery"


class Cart(models.Model):
    customer = models.ForeignKey(
        CustomerProfile,
        on_delete=models.CASCADE,
        related_name="carts",
    )
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name="carts",
    )
    delivery_type = models.CharField(
        max_length=20,
        choices=DeliveryType.choices,
        default=DeliveryType.DELIVERY,
    )

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cart"
        verbose_name_plural = "Carts"
        unique_together = ("customer", "restaurant")

    def __str__(self):
        return f"Cart({self.customer.user.email} - {self.restaurant.name})"

    @property
    def subtotal(self) -> Decimal:
        total = Decimal("0.00")
        for item in self.items.all():
            total += item.line_total
        return total

    @property
    def service_fee(self) -> Decimal:
        # TODO: Replace with real business rules / config
        return Decimal("0.00")

    @property
    def delivery_fee(self) -> Decimal:
        # TODO: Replace with real distance-based or rule-based calculation
        # For pickup, delivery fee is 0
        if self.delivery_type == DeliveryType.PICKUP:
            return Decimal("0.00")
        return Decimal("0.00")

    @property
    def total(self) -> Decimal:
        return self.subtotal + self.service_fee + self.delivery_fee


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items",
    )
    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.CASCADE,
        related_name="cart_items",
    )

    quantity = models.PositiveIntegerField(default=1)

    # Snapshot fields (so changes in menu item don't break cart)
    item_name = models.CharField(max_length=255)
    item_price = models.DecimalField(max_digits=8, decimal_places=2)
    item_image_url = models.URLField(max_length=500, null=True, blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cart Item"
        verbose_name_plural = "Cart Items"
        unique_together = ("cart", "menu_item")

    def __str__(self):
        return f"{self.item_name} x {self.quantity}"

    @property
    def line_total(self) -> Decimal:
        return self.item_price * self.quantity
