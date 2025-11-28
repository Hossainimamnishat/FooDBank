# customers/urls.py
from django.urls import path

from .views import CustomerMeView, AddressListCreateView, AddressDetailView

app_name = "customers"

urlpatterns = [
    path("me/", CustomerMeView.as_view(), name="me"),  # GET customer profile
    path("addresses/", AddressListCreateView.as_view(), name="address-list-create"),
    path("addresses/<int:pk>/", AddressDetailView.as_view(), name="address-detail"),
]
