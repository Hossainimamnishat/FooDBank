# customers/views.py
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from django.contrib.auth import get_user_model

from .models import CustomerProfile, Address
from .serializers import CustomerProfileSerializer, AddressSerializer
from accounts.models import UserRoles

User = get_user_model()


def get_or_create_customer_profile(user):
    """
    Helper to ensure the user has a CustomerProfile.
    Useful if you didn't wire signals or if role can change.
    """
    profile, created = CustomerProfile.objects.get_or_create(user=user)
    return profile


class CustomerMeView(generics.RetrieveAPIView):
    """
    Return the current authenticated customer's profile + addresses.
    """
    serializer_class = CustomerProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        user = self.request.user

        # Optional: ensure user is a customer
        if getattr(user, "role", None) != UserRoles.CUSTOMER:
            # You can raise PermissionDenied if you want to enforce role here
            # from rest_framework.exceptions import PermissionDenied
            # raise PermissionDenied("Only customers have a customer profile.")
            pass

        return get_or_create_customer_profile(user)


class AddressListCreateView(generics.ListCreateAPIView):
    """
    List and create addresses for the current customer.
    """
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        profile = get_or_create_customer_profile(self.request.user)
        return Address.objects.filter(customer=profile)

    def perform_create(self, serializer):
        profile = get_or_create_customer_profile(self.request.user)

        # If is_default=True, unset others
        is_default = serializer.validated_data.get("is_default", False)
        if is_default:
            Address.objects.filter(customer=profile, is_default=True).update(is_default=False)

        serializer.save(customer=profile)


class AddressDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a specific address of the current customer.
    """
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        profile = get_or_create_customer_profile(self.request.user)
        return Address.objects.filter(customer=profile)

    def perform_update(self, serializer):
        profile = get_or_create_customer_profile(self.request.user)
        is_default = serializer.validated_data.get("is_default", False)

        if is_default:
            Address.objects.filter(customer=profile, is_default=True).exclude(
                pk=self.get_object().pk
            ).update(is_default=False)

        serializer.save()

    def perform_destroy(self, instance):
        profile = get_or_create_customer_profile(self.request.user)

        # If deleting default, you might want to auto-assign another default
        was_default = instance.is_default
        instance.delete()

        if was_default:
            # Set newest address as default (if any exist)
            latest = Address.objects.filter(customer=profile).order_by("-created_at").first()
            if latest:
                latest.is_default = True
                latest.save()
