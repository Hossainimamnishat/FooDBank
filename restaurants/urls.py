# restaurants/urls.py
from django.urls import path

from .views import (
    RestaurantListView,
    RestaurantDetailView,
    OwnerRestaurantListCreateView,
    OwnerRestaurantDetailView,
    RestaurantOpeningHourListCreateView,
    RestaurantOpeningHourDetailView,
    AdminRestaurantApprovalView,
)

app_name = "restaurants"

urlpatterns = [
    # Public
    path("", RestaurantListView.as_view(), name="restaurant-list"),
    path("<int:pk>/", RestaurantDetailView.as_view(), name="restaurant-detail"),

    # Owner endpoints
    path("owner/", OwnerRestaurantListCreateView.as_view(), name="owner-restaurant-list-create"),
    path("owner/<int:pk>/", OwnerRestaurantDetailView.as_view(), name="owner-restaurant-detail"),

    # Opening hours management (owner)
    path(
        "owner/<int:restaurant_id>/opening-hours/",
        RestaurantOpeningHourListCreateView.as_view(),
        name="opening-hours-list-create",
    ),
    path(
        "owner/opening-hours/<int:pk>/",
        RestaurantOpeningHourDetailView.as_view(),
        name="opening-hours-detail",
    ),

    # Admin approval
    path(
        "admin/<int:pk>/approval/",
        AdminRestaurantApprovalView.as_view(),
        name="restaurant-approval",
    ),
]
