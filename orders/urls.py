# orders/urls.py
from django.urls import path

from .views import (
    CustomerOrderListView,
    CustomerOrderDetailView,
    CreateOrderFromCartView,
    RestaurantOrderListView,
    RestaurantOrderDetailView,
    RestaurantOrderStatusUpdateView,
    CustomerCancelOrderView,
    AdminOrderListView,
)

app_name = "orders"

urlpatterns = [
    # Customer: list my orders
    path("", CustomerOrderListView.as_view(), name="order-list"),

    # Customer: order detail
    path("<int:pk>/", CustomerOrderDetailView.as_view(), name="order-detail"),

    # Create order from cart for a restaurant
    path(
        "restaurants/<int:restaurant_id>/",
        CreateOrderFromCartView.as_view(),
        name="create-order-from-cart",
    ),

    # Restaurant owner: list & view orders for specific restaurant
    path(
        "restaurants/<int:restaurant_id>/list/",
        RestaurantOrderListView.as_view(),
        name="restaurant-order-list",
    ),
    path(
        "restaurants/orders/<int:pk>/",
        RestaurantOrderDetailView.as_view(),
        name="restaurant-order-detail",
    ),

    # Restaurant/admin: update order status
    path(
        "<int:pk>/status/",
        RestaurantOrderStatusUpdateView.as_view(),
        name="order-status-update",
    ),

    # Customer: cancel order
    path(
        "<int:pk>/cancel/",
        CustomerCancelOrderView.as_view(),
        name="order-cancel",
    ),

    # Admin: list all orders
    path(
        "admin/all/",
        AdminOrderListView.as_view(),
        name="admin-order-list",
    ),
]
