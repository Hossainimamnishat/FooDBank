# menus/models.py
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from restaurants.models import Restaurant


class MenuCategory(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name="menu_categories",
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Menu Category"
        verbose_name_plural = "Menu Categories"
        ordering = ["sort_order", "name"]
        unique_together = ("restaurant", "name")

    def __str__(self):
        return f"{self.name} ({self.restaurant.name})"


class MenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name="menu_items",
    )
    category = models.ForeignKey(
        MenuCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="items",
    )

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    ingredients = models.TextField(
        blank=True,
        help_text="List or description of ingredients",
    )

    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    image_url = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        help_text="URL to food picture",
    )

    quantity = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Optional stock quantity; null means unlimited",
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Whether this item is visible and orderable",
    )

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Menu Item"
        verbose_name_plural = "Menu Items"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["restaurant", "is_active"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.restaurant.name})"
