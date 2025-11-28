# orders/views.py
# orders/views.py (add near imports)
from rest_framework import permissions
from accounts.models import UserRoles

from decimal import Decimal

from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Order, OrderItem, OrderStatus, PaymentStatus
from .serializers import OrderSerializer, OrderCreateSerializer
from carts.models import Cart, DeliveryType
from customers.models import CustomerProfile, Address
from restaurants.models import Restaurant, RestaurantStatus


def get_or_create_customer_profile(user):
    profile, _ = CustomerProfile.objects.get_or_create(user=user)
    return profile

# orders/views.py (add below get_or_create_customer_profile)

class IsRestaurantOwnerOrAdmin(permissions.BasePermission):
    """
    Allow if user owns the restaurant of the order or is admin/staff.
    """

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user.is_authenticated:
            return False

        if getattr(user, "is_staff", False) or getattr(user, "role", None) == UserRoles.ADMIN:
            return True

        # obj is an Order
        return obj.restaurant.owner_id == user.id



class CustomerOrderListView(generics.ListAPIView):
    """
    GET: List orders of the authenticated customer.
    """
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        profile = get_or_create_customer_profile(self.request.user)
        qs = Order.objects.filter(customer=profile).select_related(
            "restaurant", "driver"
        ).prefetch_related("items")

        status_param = self.request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)

        return qs


class CustomerOrderDetailView(generics.RetrieveAPIView):
    """
    GET: Retrieve a single order of the authenticated customer.
    """
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        profile = get_or_create_customer_profile(self.request.user)
        return Order.objects.filter(customer=profile).select_related(
            "restaurant", "driver"
        ).prefetch_related("items")


class CreateOrderFromCartView(APIView):
    """
    POST: Create an order from the current cart for a restaurant.
    URL: /api/orders/restaurants/<restaurant_id>/
    Body:
    {
      "address_id": 1,            # required for delivery
      "delivery_type": "delivery" | "pickup",
      "delivery_note": "...",
      "tip_amount": "2.00",
      "payment_method": "paypal" | "mastercard" | "bank"
    }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, restaurant_id, *args, **kwargs):
        profile = get_or_create_customer_profile(request.user)

        restaurant = get_object_or_404(
            Restaurant,
            pk=restaurant_id,
            status__in=[RestaurantStatus.ACTIVE, RestaurantStatus.PENDING, RestaurantStatus.SUSPENDED, RestaurantStatus.REJECTED],
        )

        cart = get_object_or_404(Cart, customer=profile, restaurant=restaurant)

        if not cart.items.exists():
            return Response(
                {"detail": "Cart is empty."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        delivery_type = data["delivery_type"]
        tip_amount = data.get("tip_amount", Decimal("0.00"))
        delivery_note = data.get("delivery_note", "")
        payment_method = data["payment_method"]

        # Snapshot address (or leave blank for pickup)
        address_fields = {}
        if delivery_type == DeliveryType.DELIVERY:
            address_id = data["address_id"]
            address = get_object_or_404(
                Address,
                id=address_id,
                customer=profile,
            )
            address_fields = dict(
                address_full_name=address.full_name,
                address_phone_number=address.phone_number,
                address_street=address.street,
                address_city=address.city,
                address_postal_code=address.postal_code,
                address_country=address.country,
                address_latitude=address.latitude,
                address_longitude=address.longitude,
            )
        else:
            # pickup: address snapshot can remain blank
            address_fields = dict(
                address_full_name="",
                address_phone_number="",
                address_street="",
                address_city="",
                address_postal_code="",
                address_country="",
                address_latitude=None,
                address_longitude=None,
            )

        # Pricing (for now use cart's computed values; service & delivery are 0 in MVP)
        food_subtotal = cart.subtotal
        service_fee = cart.service_fee
        delivery_fee = cart.delivery_fee if delivery_type == DeliveryType.DELIVERY else Decimal(
            "0.00"
        )
        total_amount = food_subtotal + service_fee + delivery_fee + tip_amount

        order = Order.objects.create(
            customer=profile,
            restaurant=restaurant,
            delivery_type=delivery_type,
            delivery_note=delivery_note,
            food_subtotal=food_subtotal,
            service_fee=service_fee,
            delivery_fee=delivery_fee,
            tip_amount=tip_amount,
            total_amount=total_amount,
            payment_method=payment_method,
            payment_status=PaymentStatus.PENDING,  # will be updated by payments app
            status=OrderStatus.PENDING,
            **address_fields,
        )

        # Create OrderItems from CartItems
        for cart_item in cart.items.select_related("menu_item"):
            menu_item = cart_item.menu_item
            OrderItem.objects.create(
                order=order,
                menu_item=menu_item,
                item_name=cart_item.item_name,
                item_description=menu_item.description if menu_item else "",
                item_ingredients=menu_item.ingredients if menu_item else "",
                item_price=cart_item.item_price,
                item_image_url=cart_item.item_image_url,
                quantity=cart_item.quantity,
                line_total=cart_item.line_total,
            )

        # Clear cart after order creation (keep cart itself)
        cart.items.all().delete()

        return Response(
            OrderSerializer(order).data,
            status=status.HTTP_201_CREATED,
        )


# orders/views.py  (add these new classes)

class RestaurantOrderListView(generics.ListAPIView):
    """
    Restaurant owner: list orders for a specific restaurant.
    URL: /api/orders/restaurants/<restaurant_id>/list/
    """
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        restaurant_id = self.kwargs["restaurant_id"]

        restaurant = get_object_or_404(Restaurant, pk=restaurant_id)

        # Only owner, staff or admin can see restaurant orders
        if not (
            restaurant.owner_id == user.id
            or user.is_staff
            or getattr(user, "role", None) == UserRoles.ADMIN
        ):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You are not allowed to view these orders.")

        qs = Order.objects.filter(restaurant=restaurant).select_related(
            "customer__user", "driver"
        ).prefetch_related("items")

        status_param = self.request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)

        return qs


class RestaurantOrderDetailView(generics.RetrieveAPIView):
    """
    Restaurant owner: view a single order of their restaurant.
    """
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsRestaurantOwnerOrAdmin]
    queryset = Order.objects.select_related("restaurant", "customer__user", "driver").prefetch_related("items")

    def get_object(self):
        order = super().get_object()
        self.check_object_permissions(self.request, order)
        return order
# orders/views.py

from .serializers import (
    OrderSerializer,
    OrderCreateSerializer,
    OrderStatusUpdateSerializer,
)


class RestaurantOrderStatusUpdateView(APIView):
    """
    Restaurant owner/admin: update the status of an order.
    URL: /api/orders/<int:pk>/status/
    """
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk, *args, **kwargs):
        order = get_object_or_404(
            Order.objects.select_related("restaurant"),
            pk=pk,
        )

        # Permission check
        user = request.user
        if not (
            order.restaurant.owner_id == user.id
            or user.is_staff
            or getattr(user, "role", None) == UserRoles.ADMIN
        ):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You are not allowed to update this order.")

        serializer = OrderStatusUpdateSerializer(order, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data["status"]
        current = order.status

        # Simple transition rules (MVP)
        allowed_transitions = {
            OrderStatus.PENDING: {OrderStatus.ACCEPTED, OrderStatus.CANCELLED},
            OrderStatus.ACCEPTED: {OrderStatus.PREPARING, OrderStatus.CANCELLED},
            OrderStatus.PREPARING: {OrderStatus.READY_FOR_PICKUP, OrderStatus.CANCELLED},
            OrderStatus.READY_FOR_PICKUP: {
                OrderStatus.DRIVER_ASSIGNED,
                OrderStatus.DELIVERED,  # for pickup
            },
            OrderStatus.DRIVER_ASSIGNED: {OrderStatus.ON_THE_WAY},
            OrderStatus.ON_THE_WAY: {OrderStatus.DELIVERED},
        }

        if current in allowed_transitions and new_status not in allowed_transitions[current]:
            return Response(
                {
                    "detail": f"Invalid status transition from {current} to {new_status}."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        order.status = new_status
        order.save(update_fields=["status", "updated_at"])

        return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)
# orders/views.py

class CustomerCancelOrderView(APIView):
    """
    Customer: request cancellation of their own order.
    Simple MVP rule:
      - Can cancel if status is PENDING or ACCEPTED or PREPARING.
      - We only change order.status here; payments/refunds handled in payments app later.
    URL: /api/orders/<int:pk>/cancel/
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk, *args, **kwargs):
        profile = get_or_create_customer_profile(request.user)

        order = get_object_or_404(
            Order.objects.filter(customer=profile),
            pk=pk,
        )

        if order.status not in [
            OrderStatus.PENDING,
            OrderStatus.ACCEPTED,
            OrderStatus.PREPARING,
        ]:
            return Response(
                {"detail": "Order can no longer be cancelled at this stage."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order.status = OrderStatus.CANCELLED
        # later: trigger payments refund logic in payments app
        order.save(update_fields=["status", "updated_at"])

        return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)
class AdminOrderListView(generics.ListAPIView):
    """
    Admin/staff: list all orders in the system.
    Optional filters: ?restaurant_id= & ?status=
    """
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not (user.is_staff or getattr(user, "role", None) == UserRoles.ADMIN):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only admin/staff can view all orders.")

        qs = Order.objects.select_related("restaurant", "customer__user", "driver").prefetch_related("items")

        restaurant_id = self.request.query_params.get("restaurant_id")
        status_param = self.request.query_params.get("status")

        if restaurant_id:
            qs = qs.filter(restaurant_id=restaurant_id)
        if status_param:
            qs = qs.filter(status=status_param)

        return qs
