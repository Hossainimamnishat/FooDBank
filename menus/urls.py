# menus/urls.py
from django.urls import path

from .views import (
    PublicRestaurantMenuListView,
    OwnerMenuCategoryListCreateView,
    OwnerMenuCategoryDetailView,
    OwnerMenuItemListCreateView,
    OwnerMenuItemDetailView,
)

app_name = "menus"

urlpatterns = [
    # Public routes
    path(
        "restaurants/<int:restaurant_id>/items/",
        PublicRestaurantMenuListView.as_view(),
        name="public-restaurant-items",
    ),

    # Owner: categories
    path(
        "owner/restaurants/<int:restaurant_id>/categories/",
        OwnerMenuCategoryListCreateView.as_view(),
        name="owner-category-list-create",
    ),
    path(
        "owner/categories/<int:pk>/",
        OwnerMenuCategoryDetailView.as_view(),
        name="owner-category-detail",
    ),

    # Owner: items
    path(
        "owner/restaurants/<int:restaurant_id>/items/",
        OwnerMenuItemListCreateView.as_view(),
        name="owner-item-list-create",
    ),
    path(
        "owner/items/<int:pk>/",
        OwnerMenuItemDetailView.as_view(),
        name="owner-item-detail",
    ),
]
