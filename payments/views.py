# payments/views.py
from decimal import Decimal

from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, generics
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import PaymentTransaction, Refund, OrderCommission
from .serializers import (
    PaymentTransactionSerializer,
    RefundSerializer,
    OrderCommissionSerializer,
    PayOrderSerializer,
    RefundOrderSerializer,
)
from orders.models import Order, PaymentStatus, PaymentMethod, OrderStatus
from accounts.models import UserRoles


# You can set a global commission rate here (20% for example)
DEFAULT_COMMISSION_RATE = Decimal("0.20")


class IsAdminOrStaff(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return user and user.is_authenticated and (
            user.is_staff or getattr(user, "role", None) == UserRoles.ADMIN
        )


class PayOrderView(APIView):
    """
    POST /api/payments/orders/<order_id>/pay/

    MVP flow:
    - Ensure order is not already PAID or REFUNDED.
    - Create PaymentTransaction with status=success (simulate provider).
    - Set order.payment_status = PAID.
    - Create OrderCommission (if not already created).
    - Return order payment info + transaction.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, order_id, *args, **kwargs):
        order = get_object_or_404(Order, id=order_id)

        # Only the customer who owns the order OR admin can pay
        user = request.user
        if not (
            order.customer.user_id == user.id
            or user.is_staff
            or getattr(user, "role", None) == UserRoles.ADMIN
        ):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You are not allowed to pay this order.")

        if order.payment_status == PaymentStatus.PAID:
            return Response(
                {"detail": "Order is already paid."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if order.payment_status == PaymentStatus.REFUNDED:
            return Response(
                {"detail": "Order has been refunded and cannot be paid again."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = PayOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment_method = serializer.validated_data["payment_method"]

        # For MVP: we always charge the full total_amount
        amount = order.total_amount
        currency = order.currency

        # In real integration: call PayPal/Stripe/etc here.
        # For now we simulate a successful transaction.
        transaction = PaymentTransaction.objects.create(
            order=order,
            amount=amount,
            currency=currency,
            method=payment_method,
            status="success",  # TransactionStatus.SUCCESS
            provider_reference="SIMULATED_PROVIDER_TXN",
            raw_response={"simulated": True},
        )

        # Update order payment fields
        order.payment_method = payment_method
        order.payment_status = PaymentStatus.PAID
        order.save(update_fields=["payment_method", "payment_status", "updated_at"])

        # Create commission record if not exists
        if not hasattr(order, "commission"):
            commission_rate = DEFAULT_COMMISSION_RATE
            food_subtotal = order.food_subtotal
            commission_amount = (food_subtotal * commission_rate).quantize(
                Decimal("0.01")
            )
            restaurant_net = (food_subtotal - commission_amount).quantize(
                Decimal("0.01")
            )

            OrderCommission.objects.create(
                order=order,
                restaurant=order.restaurant,
                commission_rate=commission_rate,
                food_subtotal=food_subtotal,
                commission_amount=commission_amount,
                restaurant_net_amount=restaurant_net,
            )

        return Response(
            {
                "order_id": order.id,
                "payment_status": order.payment_status,
                "transaction": PaymentTransactionSerializer(transaction).data,
                "commission": OrderCommissionSerializer(order.commission).data,
            },
            status=status.HTTP_200_OK,
        )


class RefundOrderView(APIView):
    """
    POST /api/payments/orders/<order_id>/refund/

    MVP rules:
    - Only admin/staff OR the customer (if order cancel flow says so).
    - Only fully paid orders can be refunded.
    - We perform a full refund (amount = order.total_amount).
    - We mark order.payment_status = REFUNDED and optionally order.status = REFUNDED.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, order_id, *args, **kwargs):
        order = get_object_or_404(Order, id=order_id)

        user = request.user
        is_admin = user.is_staff or getattr(user, "role", None) == UserRoles.ADMIN
        is_order_owner = order.customer.user_id == user.id

        if not (is_admin or is_order_owner):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You are not allowed to refund this order.")

        if order.payment_status != PaymentStatus.PAID:
            return Response(
                {"detail": "Only paid orders can be refunded."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = RefundOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data.get("reason", "")

        # Find last successful transaction
        transaction = (
            order.payment_transactions.filter(status="success")
            .order_by("-created_at")
            .first()
        )
        if not transaction:
            return Response(
                {"detail": "No successful payment transaction found to refund."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        amount = order.total_amount
        currency = order.currency

        # Real world: call provider's refund API here.
        refund = Refund.objects.create(
            order=order,
            payment_transaction=transaction,
            amount=amount,
            currency=currency,
            status="success",  # RefundStatus.SUCCESS
            reason=reason,
            provider_reference="SIMULATED_PROVIDER_REFUND",
            raw_response={"simulated": True},
        )

        # Update order payment & overall status
        order.payment_status = PaymentStatus.REFUNDED
        order.status = OrderStatus.REFUNDED
        order.save(update_fields=["payment_status", "status", "updated_at"])

        return Response(
            {
                "order_id": order.id,
                "payment_status": order.payment_status,
                "order_status": order.status,
                "refund": RefundSerializer(refund).data,
            },
            status=status.HTTP_200_OK,
        )


# ---------- Admin views (optional but useful) ----------


class AdminPaymentTransactionListView(generics.ListAPIView):
    """
    Admin/staff: list all payment transactions. Optional filters:
    - ?order_id=
    - ?status=success|failed|pending
    """
    serializer_class = PaymentTransactionSerializer
    permission_classes = [IsAdminOrStaff]

    def get_queryset(self):
        qs = PaymentTransaction.objects.select_related("order", "order__restaurant")

        order_id = self.request.query_params.get("order_id")
        status_param = self.request.query_params.get("status")

        if order_id:
            qs = qs.filter(order_id=order_id)
        if status_param:
            qs = qs.filter(status=status_param)

        return qs


class AdminRefundListView(generics.ListAPIView):
    """
    Admin/staff: list all refunds.
    Optional filters: ?order_id= & ?status=
    """
    serializer_class = RefundSerializer
    permission_classes = [IsAdminOrStaff]

    def get_queryset(self):
        qs = Refund.objects.select_related("order")

        order_id = self.request.query_params.get("order_id")
        status_param = self.request.query_params.get("status")

        if order_id:
            qs = qs.filter(order_id=order_id)
        if status_param:
            qs = qs.filter(status=status_param)

        return qs


class AdminOrderCommissionListView(generics.ListAPIView):
    """
    Admin/staff: list all commissions.
    Optional filters: ?restaurant_id= & ?order_id=
    """
    serializer_class = OrderCommissionSerializer
    permission_classes = [IsAdminOrStaff]

    def get_queryset(self):
        qs = OrderCommission.objects.select_related("order", "restaurant")

        restaurant_id = self.request.query_params.get("restaurant_id")
        order_id = self.request.query_params.get("order_id")

        if restaurant_id:
            qs = qs.filter(restaurant_id=restaurant_id)
        if order_id:
            qs = qs.filter(order_id=order_id)

        return qs
