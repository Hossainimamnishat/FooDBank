# restaurants/models.py
from django.conf import settings
from django.db import models
from django.utils import timezone


class RestaurantStatus(models.TextChoices):
    PENDING = "pending", "Pending Approval"
    ACTIVE = "active", "Active"
    REJECTED = "rejected", "Rejected"
    SUSPENDED = "suspended", "Suspended"


class Restaurant(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="restaurants_owned",
    )

    name = models.CharField(max_length=255)
    licence_number = models.CharField(
        max_length=100,
        help_text="Valid restaurant licence number",
    )
    phone_number = models.CharField(max_length=20)
    email = models.EmailField()

    banner_image = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        help_text="URL to banner image",
    )
    logo_image = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        help_text="URL to logo image",
    )

    # Address
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default="Germany")

    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    status = models.CharField(
        max_length=20,
        choices=RestaurantStatus.choices,
        default=RestaurantStatus.PENDING,
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the restaurant is currently accepting orders",
    )

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Restaurant"
        verbose_name_plural = "Restaurants"
        indexes = [
            models.Index(fields=["city", "postal_code"]),
            models.Index(fields=["status", "is_active"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.city})"


class RestaurantOpeningHour(models.Model):
    """
    Opening & closing hours per day of week.
    day_of_week: 0 = Monday, 6 = Sunday
    """

    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6

    DAY_OF_WEEK_CHOICES = [
        (MONDAY, "Monday"),
        (TUESDAY, "Tuesday"),
        (WEDNESDAY, "Wednesday"),
        (THURSDAY, "Thursday"),
        (FRIDAY, "Friday"),
        (SATURDAY, "Saturday"),
        (SUNDAY, "Sunday"),
    ]

    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name="opening_hours",
    )
    day_of_week = models.IntegerField(choices=DAY_OF_WEEK_CHOICES)
    open_time = models.TimeField(null=True, blank=True)
    close_time = models.TimeField(null=True, blank=True)
    is_closed = models.BooleanField(
        default=False,
        help_text="If True, restaurant is closed this day.",
    )

    class Meta:
        verbose_name = "Restaurant Opening Hour"
        verbose_name_plural = "Restaurant Opening Hours"
        unique_together = ("restaurant", "day_of_week")
        ordering = ["day_of_week"]

    def __str__(self):
        return f"{self.restaurant.name} - {self.get_day_of_week_display()}"
