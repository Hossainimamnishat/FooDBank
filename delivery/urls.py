# delivery/urls.py
from django.urls import path

from .views import (
    DriverMeView,
    DriverShiftListView,
    DriverShiftStartView,
    DriverShiftEndView,
    AvailableOrdersForDriverView,
    DriverAcceptOrderView,
    DriverOrderStatusUpdateView,
)

app_name = "delivery"

urlpatterns = [
    # Driver profile
    path("me/", DriverMeView.as_view(), name="driver-me"),

    # Shifts
    path("shifts/", DriverShiftListView.as_view(), name="driver-shift-list"),
    path("shifts/start/", DriverShiftStartView.as_view(), name="driver-shift-start"),
    path("shifts/end/", DriverShiftEndView.as_view(), name="driver-shift-end"),

    # Orders
    path(
        "orders/available/",
        AvailableOrdersForDriverView.as_view(),
        name="available-orders",
    ),
    path(
        "orders/<int:order_id>/accept/",
        DriverAcceptOrderView.as_view(),
        name="accept-order",
    ),
    path(
        "orders/<int:order_id>/status/",
        DriverOrderStatusUpdateView.as_view(),
        name="driver-order-status",
    ),
]
