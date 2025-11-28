# delivery/views.py
import math
from decimal import Decimal

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, status, generics
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import DriverProfile, DriverShift, DeliveryAssignment, VehicleType
from .serializers import (
    DriverProfileSerializer,
    DriverProfileUpdateSerializer,
    DriverShiftSerializer,
    DeliveryAssignmentSerializer,
)
from accounts.models import UserRoles
from orders.models import Order, OrderStatus
from carts.models import DeliveryType
from restaurants.models import Restaurant


def get_or_create_driver_profile(user):
    profile, _ = DriverProfile.objects.get_or_create(
        user=user,
        defaults={
            "vehicle_type": VehicleType.BIKE,
            "service_area_city": "",
        },
    )
    return profile


def haversine_distance_km(lat1, lon1, lat2, lon2):
    """
    Compute distance in km between two lat/long points.
    """
    if None in (lat1, lon1, lat2, lon2):
        return None

    R = 6371.0  # Earth radius in km
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


class IsDriver(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return (
            user
            and user.is_authenticated
            and getattr(user, "role", None) == UserRoles.DRIVER
        )


# ---------- DRIVER PROFILE ----------


class DriverMeView(APIView):
    """
    GET: my driver profile
    PATCH: update my driver profile (vehicle, service area)
    """
    permission_classes = [permissions.IsAuthenticated, IsDriver]

    def get(self, request, *args, **kwargs):
        profile = get_or_create_driver_profile(request.user)
        return Response(
            DriverProfileSerializer(profile).data, status=status.HTTP_200_OK
        )

    def patch(self, request, *args, **kwargs):
        profile = get_or_create_driver_profile(request.user)
        serializer = DriverProfileUpdateSerializer(
            profile, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            DriverProfileSerializer(profile).data, status=status.HTTP_200_OK
        )


# ---------- SHIFTS ----------


class DriverShiftListView(generics.ListAPIView):
    """
    GET: list my shifts
    """
    serializer_class = DriverShiftSerializer
    permission_classes = [permissions.IsAuthenticated, IsDriver]

    def get_queryset(self):
        profile = get_or_create_driver_profile(self.request.user)
        return DriverShift.objects.filter(driver=profile)


class DriverShiftStartView(APIView):
    """
    POST: start a shift
    """
    permission_classes = [permissions.IsAuthenticated, IsDriver]

    def post(self, request, *args, **kwargs):
        profile = get_or_create_driver_profile(request.user)

        # If there is already an open shift, don't start a new one
        open_shift = (
            DriverShift.objects.filter(driver=profile, end_time__isnull=True)
            .order_by("-start_time")
            .first()
        )
        if open_shift:
            return Response(
                {"detail": "You already have an open shift."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        shift = DriverShift.objects.create(
            driver=profile,
            start_time=timezone.now(),
        )
        return Response(
            DriverShiftSerializer(shift).data,
            status=status.HTTP_201_CREATED,
        )


class DriverShiftEndView(APIView):
    """
    POST: end the current shift
    """
    permission_classes = [permissions.IsAuthenticated, IsDriver]

    def post(self, request, *args, **kwargs):
        profile = get_or_create_driver_profile(request.user)

        shift = (
            DriverShift.objects.filter(driver=profile, end_time__isnull=True)
            .order_by("-start_time")
            .first()
        )
        if not shift:
            return Response(
                {"detail": "You do not have an open shift."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        shift.close_shift()
        return Response(
            DriverShiftSerializer(shift).data,
            status=status.HTTP_200_OK,
        )


# ---------- ORDER ASSIGNMENT & STATUS ----------


class AvailableOrdersForDriverView(generics.ListAPIView):
    """
    GET: list available delivery orders for this driver.
    MVP criteria:
      - delivery_type = delivery
      - status = ready_for_pickup
      - driver is null
      - same city as driver.service_area_city if set
    """
    serializer_class =  None  # we'll reuse OrderSerializer dynamically
    permission_classes = [permissions.IsAuthenticated, IsDriver]

    def get_serializer_class(self):
        from orders.serializers import OrderSerializer
        return OrderSerializer

    def get_queryset(self):
        profile = get_or_create_driver_profile(self.request.user)

        qs = Order.objects.filter(
            delivery_type=DeliveryType.DELIVERY,
            status=OrderStatus.READY_FOR_PICKUP,
            driver__isnull=True,
        ).select_related("restaurant", "customer__user")

        if profile.service_area_city:
            qs = qs.filter(restaurant__city__iexact=profile.service_area_city)

        return qs


class DriverAcceptOrderView(APIView):
    """
    POST: driver accepts an available order (assign to self).
    - sets order.driver
    - sets order.status = driver_assigned (if allowed)
    - creates DeliveryAssignment with distance & per-km pay
    """
    permission_classes = [permissions.IsAuthenticated, IsDriver]

    def post(self, request, order_id, *args, **kwargs):
        profile = get_or_create_driver_profile(request.user)

        order = get_object_or_404(Order, id=order_id)

        if order.delivery_type != DeliveryType.DELIVERY:
            return Response(
                {"detail": "Only delivery orders can be assigned to drivers."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if order.driver is not None:
            return Response(
                {"detail": "Order already has a driver assigned."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if order.status not in [OrderStatus.READY_FOR_PICKUP]:
            return Response(
                {"detail": "Order is not ready for pickup."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Optional city filter: ensure driver service city matches restaurant city
        if profile.service_area_city and (
            order.restaurant.city.lower() != profile.service_area_city.lower()
        ):
            return Response(
                {"detail": "Order is outside your service area."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Basic distance calc between restaurant and delivery address
        distance_km = None
        if order.delivery_type == DeliveryType.DELIVERY:
            lat1 = order.restaurant.latitude
            lon1 = order.restaurant.longitude
            lat2 = order.address_latitude
            lon2 = order.address_longitude
            distance_km = haversine_distance_km(lat1, lon1, lat2, lon2)

        if distance_km is None:
            distance_km = 0.0

        # Enforce max distance depending on vehicle type
        max_km = 15.0 if profile.vehicle_type == VehicleType.CAR else 8.0
        if distance_km > max_km:
            return Response(
                {
                    "detail": f"Order distance ({distance_km:.1f} km) exceeds your vehicle limit ({max_km} km)."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create assignment
        per_km_rate = profile.per_km_rate
        distance_pay = Decimal(str(distance_km)) * per_km_rate

        assignment = DeliveryAssignment.objects.create(
            order=order,
            driver=profile,
            distance_km=distance_km,
            per_km_rate=per_km_rate,
            distance_pay=distance_pay,
        )

        # Attach driver to order & update status
        order.driver = profile
        order.status = OrderStatus.DRIVER_ASSIGNED
        order.save(update_fields=["driver", "status", "updated_at"])

        from orders.serializers import OrderSerializer
        return Response(
            {
                "order": OrderSerializer(order).data,
                "assignment": DeliveryAssignmentSerializer(assignment).data,
            },
            status=status.HTTP_200_OK,
        )


class DriverOrderStatusUpdateView(APIView):
    """
    POST: driver updates status of their order.
    Allowed transitions (for driver):
      - driver_assigned -> on_the_way
      - on_the_way -> delivered
    """
    permission_classes = [permissions.IsAuthenticated, IsDriver]

    def post(self, request, order_id, *args, **kwargs):
        profile = get_or_create_driver_profile(request.user)

        order = get_object_or_404(Order, id=order_id, driver=profile)

        new_status = request.data.get("status")
        if new_status not in [OrderStatus.ON_THE_WAY, OrderStatus.DELIVERED]:
            return Response(
                {"detail": "Driver can only set status to 'on_the_way' or 'delivered'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        current = order.status
        if current == OrderStatus.DRIVER_ASSIGNED and new_status != OrderStatus.ON_THE_WAY:
            return Response(
                {
                    "detail": f"Invalid transition from {current} to {new_status}. Must go to 'on_the_way' first."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if current == OrderStatus.ON_THE_WAY and new_status != OrderStatus.DELIVERED:
            return Response(
                {
                    "detail": f"Invalid transition from {current} to {new_status}. Must go to 'delivered'."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if current not in [OrderStatus.DRIVER_ASSIGNED, OrderStatus.ON_THE_WAY]:
            return Response(
                {"detail": "Order is not in a state the driver can update."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order.status = new_status
        order.save(update_fields=["status", "updated_at"])

        from orders.serializers import OrderSerializer
        return Response(
            OrderSerializer(order).data,
            status=status.HTTP_200_OK,
        )
