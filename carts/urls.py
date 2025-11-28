# carts/urls.py
from django.urls import path

from .views import (
    CartDetailView,
    CartDeliveryTypeUpdateView,
    CartAddItemView,
    CartRemoveItemView,
    CartClearView,
    CartSuggestionsView,
)

app_name = "carts"

urlpatterns = [
    # Get cart for a restaurant
    path(
        "restaurants/<int:restaurant_id>/",
        CartDetailView.as_view(),
        name="cart-detail",
    ),

    # Update delivery type (pickup/delivery)
    path(
        "restaurants/<int:restaurant_id>/delivery-type/",
        CartDeliveryTypeUpdateView.as_view(),
        name="cart-delivery-type",
    ),

    # Add or update item
    path(
        "restaurants/<int:restaurant_id>/items/",
        CartAddItemView.as_view(),
        name="cart-add-item",
    ),

    # Remove one item
    path(
        "restaurants/<int:restaurant_id>/items/<int:item_id>/",
        CartRemoveItemView.as_view(),
        name="cart-remove-item",
    ),

    # Clear all items
    path(
        "restaurants/<int:restaurant_id>/clear/",
        CartClearView.as_view(),
        name="cart-clear",
    ),

    # Suggestions
    path(
        "restaurants/<int:restaurant_id>/suggestions/",
        CartSuggestionsView.as_view(),
        name="cart-suggestions",
    ),
]
