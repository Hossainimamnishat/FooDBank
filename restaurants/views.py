# restaurants/views.py
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from .models import Restaurant, RestaurantOpeningHour, RestaurantStatus
from .serializers import (
    RestaurantSerializer,
    RestaurantCreateUpdateSerializer,
    RestaurantOpeningHourSerializer,
)
from accounts.models import UserRoles
from django.contrib.auth import get_user_model

User = get_user_model()


class IsRestaurantOwnerOrAdmin(permissions.BasePermission):
    """
    Allow access if the user is the restaurant owner or an admin/staff.
    """

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user.is_authenticated:
            return False

        if getattr(user, "is_staff", False) or getattr(user, "role", None) == UserRoles.ADMIN:
            return True

        # obj can be Restaurant or RestaurantOpeningHour
        if isinstance(obj, Restaurant):
            return obj.owner_id == user.id
        if isinstance(obj, RestaurantOpeningHour):
            return obj.restaurant.owner_id == user.id

        return False


# ---------- PUBLIC VIEWS ----------


class RestaurantListView(generics.ListAPIView):
    """
    Public list of restaurants that are active and approved.
    """
    serializer_class = RestaurantSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = Restaurant.objects.filter(
            status=RestaurantStatus.ACTIVE,
            is_active=True,
        )
        city = self.request.query_params.get("city")
        postal_code = self.request.query_params.get("postal_code")

        if city:
            qs = qs.filter(city__iexact=city)
        if postal_code:
            qs = qs.filter(postal_code__iexact=postal_code)

        return qs


class RestaurantDetailView(generics.RetrieveAPIView):
    """
    Public restaurant detail.
    Only returns if restaurant is approved & active.
    """
    serializer_class = RestaurantSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Restaurant.objects.filter(
        status=RestaurantStatus.ACTIVE,
        is_active=True,
    )


# ---------- OWNER VIEWS ----------


class OwnerRestaurantListCreateView(generics.ListCreateAPIView):
    """
    Restaurant owner: list and create their restaurants.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Restaurant.objects.filter(owner=user)

    def get_serializer_class(self):
        if self.request.method == "GET":
            return RestaurantSerializer
        return RestaurantCreateUpdateSerializer

    def perform_create(self, serializer):
        user = self.request.user
        # Ensure user has restaurant_owner role
        if getattr(user, "role", None) != UserRoles.RESTAURANT_OWNER and not user.is_staff:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only restaurant owners can create restaurants.")

        # New restaurants start as pending
        serializer.save(
            owner=user,
            status=RestaurantStatus.PENDING,
        )


class OwnerRestaurantDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Restaurant owner: manage their own restaurant.
    """
    permission_classes = [permissions.IsAuthenticated, IsRestaurantOwnerOrAdmin]
    queryset = Restaurant.objects.all()

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return RestaurantCreateUpdateSerializer
        return RestaurantSerializer

    def get_object(self):
        restaurant = super().get_object()
        self.check_object_permissions(self.request, restaurant)
        return restaurant


class RestaurantOpeningHourListCreateView(generics.ListCreateAPIView):
    """
    Restaurant owner: list/create opening hours for a given restaurant.
    """
    serializer_class = RestaurantOpeningHourSerializer
    permission_classes = [permissions.IsAuthenticated, IsRestaurantOwnerOrAdmin]

    def get_queryset(self):
        restaurant_id = self.kwargs["restaurant_id"]
        restaurant = get_object_or_404(Restaurant, pk=restaurant_id)
        self.check_object_permissions(self.request, restaurant)
        return RestaurantOpeningHour.objects.filter(restaurant=restaurant)

    def perform_create(self, serializer):
        restaurant_id = self.kwargs["restaurant_id"]
        restaurant = get_object_or_404(Restaurant, pk=restaurant_id)
        self.check_object_permissions(self.request, restaurant)
        serializer.save(restaurant=restaurant)


class RestaurantOpeningHourDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Restaurant owner: retrieve/update/delete a specific opening hour.
    """
    serializer_class = RestaurantOpeningHourSerializer
    permission_classes = [permissions.IsAuthenticated, IsRestaurantOwnerOrAdmin]
    queryset = RestaurantOpeningHour.objects.select_related("restaurant")

    def get_object(self):
        opening_hour = super().get_object()
        # Permission based on its restaurant
        self.check_object_permissions(self.request, opening_hour)
        return opening_hour


# ---------- ADMIN VIEWS ----------


class AdminRestaurantApprovalView(APIView):
    """
    Admin/staff: approve or reject a restaurant.
    POST with {"status": "active"} or {"status": "rejected"}.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk, *args, **kwargs):
        user = request.user
        if not (user.is_staff or getattr(user, "role", None) == UserRoles.ADMIN):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only admin can approve or reject restaurants.")

        restaurant = get_object_or_404(Restaurant, pk=pk)
        new_status = request.data.get("status")

        if new_status not in [RestaurantStatus.ACTIVE, RestaurantStatus.REJECTED, RestaurantStatus.SUSPENDED]:
            return Response(
                {"detail": "Invalid status value."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        restaurant.status = new_status
        restaurant.save(update_fields=["status"])

        return Response(
            RestaurantSerializer(restaurant).data,
            status=status.HTTP_200_OK,
        )
