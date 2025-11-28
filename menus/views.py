# menus/views.py
from rest_framework import generics, permissions
from django.shortcuts import get_object_or_404

from .models import MenuCategory, MenuItem
from .serializers import (
    MenuCategorySerializer,
    MenuItemSerializer,
    MenuItemCreateUpdateSerializer,
)
from restaurants.models import Restaurant, RestaurantStatus
from accounts.models import UserRoles


class IsRestaurantOwnerOrAdmin(permissions.BasePermission):
    """
    Allow if user owns the restaurant or is admin/staff.
    """

    def has_permission(self, request, view):
        # For list/create, we check in get_queryset/perform_create
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user.is_authenticated:
            return False

        if getattr(user, "is_staff", False) or getattr(user, "role", None) == UserRoles.ADMIN:
            return True

        # obj can be MenuCategory, MenuItem
        restaurant = None
        if isinstance(obj, MenuCategory):
            restaurant = obj.restaurant
        elif isinstance(obj, MenuItem):
            restaurant = obj.restaurant

        if restaurant is None:
            return False

        return restaurant.owner_id == user.id


# ---------- PUBLIC VIEWS ----------


class PublicRestaurantMenuListView(generics.ListAPIView):
    """
    Public: list active menu items for a restaurant.
    Optional: filter by category ?category_id=
    """
    serializer_class = MenuItemSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        restaurant_id = self.kwargs["restaurant_id"]
        restaurant = get_object_or_404(
            Restaurant,
            pk=restaurant_id,
            status=RestaurantStatus.ACTIVE,
            is_active=True,
        )

        qs = MenuItem.objects.filter(
            restaurant=restaurant,
            is_active=True,
        ).select_related("category")

        category_id = self.request.query_params.get("category_id")
        if category_id:
            qs = qs.filter(category_id=category_id)

        return qs


# ---------- OWNER CATEGORY VIEWS ----------


class OwnerMenuCategoryListCreateView(generics.ListCreateAPIView):
    """
    Owner: list/create categories for a given restaurant.
    """
    serializer_class = MenuCategorySerializer
    permission_classes = [permissions.IsAuthenticated, IsRestaurantOwnerOrAdmin]

    def get_queryset(self):
        restaurant_id = self.kwargs["restaurant_id"]
        restaurant = get_object_or_404(Restaurant, pk=restaurant_id)
        # check owner/admin
        self.check_object_permissions(self.request, restaurant)
        return MenuCategory.objects.filter(restaurant=restaurant)

    def perform_create(self, serializer):
        restaurant_id = self.kwargs["restaurant_id"]
        restaurant = get_object_or_404(Restaurant, pk=restaurant_id)
        self.check_object_permissions(self.request, restaurant)
        serializer.save(restaurant=restaurant)


class OwnerMenuCategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Owner: manage a single category.
    """
    serializer_class = MenuCategorySerializer
    permission_classes = [permissions.IsAuthenticated, IsRestaurantOwnerOrAdmin]
    queryset = MenuCategory.objects.select_related("restaurant")

    def get_object(self):
        category = super().get_object()
        self.check_object_permissions(self.request, category)
        return category


# ---------- OWNER ITEM VIEWS ----------


class OwnerMenuItemListCreateView(generics.ListCreateAPIView):
    """
    Owner: list/create menu items for a given restaurant.
    """
    permission_classes = [permissions.IsAuthenticated, IsRestaurantOwnerOrAdmin]

    def get_queryset(self):
        restaurant_id = self.kwargs["restaurant_id"]
        restaurant = get_object_or_404(Restaurant, pk=restaurant_id)
        self.check_object_permissions(self.request, restaurant)
        return MenuItem.objects.filter(restaurant=restaurant).select_related("category")

    def get_serializer_class(self):
        if self.request.method == "GET":
            return MenuItemSerializer
        return MenuItemCreateUpdateSerializer

    def perform_create(self, serializer):
        restaurant_id = self.kwargs["restaurant_id"]
        restaurant = get_object_or_404(Restaurant, pk=restaurant_id)
        self.check_object_permissions(self.request, restaurant)

        # If category is set, enforce it belongs to same restaurant
        category = serializer.validated_data.get("category")
        if category and category.restaurant_id != restaurant.id:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("Category does not belong to this restaurant.")

        serializer.save(restaurant=restaurant)


class OwnerMenuItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Owner: manage a single menu item.
    """
    permission_classes = [permissions.IsAuthenticated, IsRestaurantOwnerOrAdmin]
    queryset = MenuItem.objects.select_related("restaurant", "category")

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return MenuItemCreateUpdateSerializer
        return MenuItemSerializer

    def get_object(self):
        item = super().get_object()
        self.check_object_permissions(self.request, item)
        return item

    def perform_update(self, serializer):
        item = self.get_object()
        restaurant = item.restaurant

        category = serializer.validated_data.get("category")
        if category and category.restaurant_id != restaurant.id:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("Category does not belong to this restaurant.")

        serializer.save()
