# payments/urls.py
from django.urls import path

from .views import (
    PayOrderView,
    RefundOrderView,
    AdminPaymentTransactionListView,
    AdminRefundListView,
    AdminOrderCommissionListView,
)

app_name = "payments"

urlpatterns = [
    # Pay & refund
    path("orders/<int:order_id>/pay/", PayOrderView.as_view(), name="pay-order"),
    path("orders/<int:order_id>/refund/", RefundOrderView.as_view(), name="refund-order"),

    # Admin listings
    path(
        "admin/transactions/",
        AdminPaymentTransactionListView.as_view(),
        name="admin-transactions",
    ),
    path(
        "admin/refunds/",
        AdminRefundListView.as_view(),
        name="admin-refunds",
    ),
    path(
        "admin/commissions/",
        AdminOrderCommissionListView.as_view(),
        name="admin-commissions",
    ),
]
