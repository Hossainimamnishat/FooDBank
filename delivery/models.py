# delivery/models.py
from decimal import Decimal
from django.conf import settings
from django.db import models
from django.utils import timezone

from restaurants.models import Restaurant


class VehicleType(models.TextChoices):
    BIKE = "bike", "Bicycle"
    CAR = "car", "Car"


class DriverProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="driver_profile",
    )
    vehicle_type = models.CharField(
        max_length=10,
        choices=VehicleType.choices,
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the driver is active/onboarded on the platform.",
    )

    # Pay settings
    hourly_rate = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal("12.00"),
        help_text="Hourly pay in EUR.",
    )
    per_km_rate = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal("0.15"),
        help_text="Per km pay in EUR, especially for bicycles.",
    )

    # Delivery radius / geoboundary (simple MVP)
    service_area_city = models.CharField(
        max_length=100,
        blank=True,
        help_text="City where driver usually works.",
    )
    service_radius_km = models.FloatField(
        default=15.0,
        help_text="Max distance (km) for orders from driver's base.",
    )

    # Optional driver location (not fully used yet, but ready)
    home_latitude = models.FloatField(null=True, blank=True)
    home_longitude = models.FloatField(null=True, blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Driver Profile"
        verbose_name_plural = "Driver Profiles"

    def __str__(self):
        return f"DriverProfile({self.user.email}, {self.vehicle_type})"


class DriverShift(models.Model):
    driver = models.ForeignKey(
        DriverProfile,
        on_delete=models.CASCADE,
        related_name="shifts",
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    total_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Computed when shift ends.",
    )

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Driver Shift"
        verbose_name_plural = "Driver Shifts"
        ordering = ["-start_time"]

    def __str__(self):
        return f"Shift({self.driver.user.email}, {self.start_time} - {self.end_time})"

    @property
    def is_open(self) -> bool:
        return self.end_time is None

    def close_shift(self, end_time=None):
        if end_time is None:
            end_time = timezone.now()
        self.end_time = end_time
        duration = self.end_time - self.start_time
        self.total_minutes = max(int(duration.total_seconds() // 60), 0)
        self.save(update_fields=["end_time", "total_minutes"])


class DeliveryAssignment(models.Model):
    """
    Represents the assignment of an order to a driver,
    including distance and calculated pay for that job.
    """

    order = models.OneToOneField(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="delivery_assignment",
    )
    driver = models.ForeignKey(
        DriverProfile,
        on_delete=models.CASCADE,
        related_name="assignments",
    )

    distance_km = models.FloatField(
        help_text="Distance used for pay calculation (km).",
    )
    per_km_rate = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        help_text="Per km rate applied for this order.",
    )
    distance_pay = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="distance_km * per_km_rate",
    )

    # Optional bonus per order (e.g. for peak hours)
    bonus_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Delivery Assignment"
        verbose_name_plural = "Delivery Assignments"

    def __str__(self):
        return f"Assignment(Order #{self.order_id}, Driver {self.driver.user.email})"
