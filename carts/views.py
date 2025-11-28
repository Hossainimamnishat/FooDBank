# carts/views.py
from decimal import Decimal

from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Cart, CartItem, DeliveryType
from .serializers import (
    CartSerializer,
    CartDeliveryTypeUpdateSerializer,
    AddOrUpdateCartItemSerializer,
    CartItemSerializer,
)
from customers.models import CustomerProfile
from menus.models import MenuItem
from menus.serializers import MenuItemSerializer  # reuse public menu serializer
from restaurants.models import Restaurant, RestaurantStatus


def get_or_create_customer_profile(user):
    profile, _ = CustomerProfile.objects.get_or_create(user=user)
    return profile


def get_or_create_cart_for_restaurant(user, restaurant_id):
    profile = get_or_create_customer_profile(user)
    restaurant = get_object_or_404(
        Restaurant,
        pk=restaurant_id,
        status__in=[RestaurantStatus.ACTIVE, RestaurantStatus.PENDING, RestaurantStatus.SUSPENDED, RestaurantStatus.REJECTED],
    )
    cart, _ = Cart.objects.get_or_create(
        customer=profile,
        restaurant=restaurant,
        defaults={"delivery_type": DeliveryType.DELIVERY},
    )
    return cart


class CartDetailView(APIView):
    """
    GET: Return current cart for the given restaurant (creates empty cart if none).
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, restaurant_id, *args, **kwargs):
        cart = get_or_create_cart_for_restaurant(request.user, restaurant_id)
        return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)


class CartDeliveryTypeUpdateView(APIView):
    """
    PATCH: Update delivery type (pickup/delivery) for this cart.
    """
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, restaurant_id, *args, **kwargs):
        cart = get_or_create_cart_for_restaurant(request.user, restaurant_id)
        serializer = CartDeliveryTypeUpdateSerializer(cart, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)


class CartAddItemView(APIView):
    """
    POST: Add or update an item in the cart.
    Body: { "menu_item_id": <int>, "quantity": <int> }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, restaurant_id, *args, **kwargs):
        cart = get_or_create_cart_for_restaurant(request.user, restaurant_id)

        serializer = AddOrUpdateCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        menu_item_id = serializer.validated_data["menu_item_id"]
        quantity = serializer.validated_data["quantity"]

        menu_item = get_object_or_404(MenuItem, id=menu_item_id, is_active=True)

        # Ensure the menu item belongs to the same restaurant
        if menu_item.restaurant_id != cart.restaurant_id:
            return Response(
                {"detail": "Menu item does not belong to this restaurant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            menu_item=menu_item,
            defaults={
                "quantity": quantity,
                "item_name": menu_item.name,
                "item_price": menu_item.price,
                "item_image_url": menu_item.image_url,
            },
        )

        if not created:
            cart_item.quantity = quantity
            # Optionally refresh snapshot price/name
            cart_item.item_name = menu_item.name
            cart_item.item_price = menu_item.price
            cart_item.item_image_url = menu_item.image_url
            cart_item.save()

        cart.refresh_from_db()
        return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)


class CartRemoveItemView(APIView):
    """
    DELETE: Remove a specific item from the cart.
    """
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, restaurant_id, item_id, *args, **kwargs):
        cart = get_or_create_cart_for_restaurant(request.user, restaurant_id)
        cart_item = get_object_or_404(CartItem, cart=cart, id=item_id)
        cart_item.delete()
        cart.refresh_from_db()
        return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)


class CartClearView(APIView):
    """
    DELETE: Clear all items from the cart for this restaurant.
    """
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, restaurant_id, *args, **kwargs):
        cart = get_or_create_cart_for_restaurant(request.user, restaurant_id)
        cart.items.all().delete()
        cart.refresh_from_db()
        return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)


class CartSuggestionsView(APIView):
    """
    GET: Suggest "better items" for the cart.
    Simple MVP strategy:
      - Same restaurant
      - Active items
      - Not already in the cart
      - Optionally same category as first cart item
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, restaurant_id, *args, **kwargs):
        cart = get_or_create_cart_for_restaurant(request.user, restaurant_id)

        # IDs of items already in cart
        in_cart_ids = cart.items.values_list("menu_item_id", flat=True)

        qs = MenuItem.objects.filter(
            restaurant=cart.restaurant,
            is_active=True,
        ).exclude(id__in=in_cart_ids)

        # Optional: prioritize same category as first cart item
        first_cart_item = cart.items.first()
        if first_cart_item and first_cart_item.menu_item.category_id:
            qs = qs.order_by("-category_id")

        # MVP: limit to, say, 5 suggestions
        suggestions = qs[:5]

        data = MenuItemSerializer(suggestions, many=True).data
        return Response(data, status=status.HTTP_200_OK)
