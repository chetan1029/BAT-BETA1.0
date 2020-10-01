"""URL Patterns for Setting app."""

from django.urls import path

from . import views

app_name = "setting"

urlpatterns = [
    # global Settings
    # Payment Terms
    path(
        "payment-terms",
        views.PaymentTermsListView.as_view(),
        name="paymentterms_list",
    ),
    path(
        "payment-terms/add",
        views.CreatePaymentTermsView.as_view(),
        name="create_paymentterms",
    ),
    path(
        "payment-terms/<int:pk>/edit/",
        views.PaymentTermsUpdateView.as_view(),
        name="update_paymentterms",
    ),
    path(
        "payment-terms/<int:pk>/delete/",
        views.PaymentTermsDeleteView.as_view(),
        name="delete_paymentterms",
    ),
]
