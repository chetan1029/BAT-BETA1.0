"""View class and functions for Setting app."""

import logging
from decimal import Decimal

from bat.setting.forms import PaymentTermsForm
from bat.setting.models import PaymentTerms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models.deletion import ProtectedError
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView
from rolepermissions.mixins import HasPermissionsMixin

logger = logging.getLogger(__name__)

# Global Variable
CAT_PRODUCT = "Products"


# Create Mixins
class PaymentTermsMenuMixin:
    """Mixing For Payment Terms Menu."""

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        context["active_menu"] = {
            "dashboard": "global",
            "menu1": "setting",
            "menu2": "paymentterms",
        }
        return context


class DeleteMixin:
    """
    Mixing to use while deleting data.

    I found some time we have to use same set of delete method for many CBV so
    I decided to make a mixin and pass that mixin to all delete views.
    """

    def delete(self, request, *args, **kwargs):
        """Delete method to define error messages."""
        obj = self.get_object()
        get_success_url = self.get_success_url()
        get_error_url = self.get_error_url()
        try:
            obj.delete()
            messages.success(self.request, self.success_message % obj.__dict__)
            return HttpResponseRedirect(get_success_url)
        except ProtectedError:
            messages.warning(self.request, self.protected_error % obj.__dict__)
            return HttpResponseRedirect(get_error_url)


# Create your views here.
class PaymentTermsListView(
    HasPermissionsMixin, LoginRequiredMixin, PaymentTermsMenuMixin, ListView
):
    """List all the payment terms."""

    required_permission = "view_payment_terms"
    model = PaymentTerms
    template_name = "setting/paymentterms/paymentterms_list.html"


class CreatePaymentTermsView(
    HasPermissionsMixin,
    LoginRequiredMixin,
    PaymentTermsMenuMixin,
    SuccessMessageMixin,
    CreateView,
):
    """Create Payment terms."""

    required_permission = "add_payment_terms"
    form_class = PaymentTermsForm
    model = PaymentTerms
    success_message = "Payment terms was created successfully"
    template_name = "setting/paymentterms/paymentterms_form.html"

    def form_valid(self, form):
        """If form is valid update title."""
        self.object = form.save(commit=False)
        deposit = Decimal(self.object.deposit)
        on_delivery = Decimal(self.object.on_delivery)
        receiving = Decimal(self.object.receiving)
        remaining_per = Decimal(100) - (deposit + on_delivery + receiving)
        self.object.remaining = remaining_per
        self.object.title = (
            "PAY"
            + str(self.object.deposit)
            + "-"
            + str(self.object.on_delivery)
            + "-"
            + str(self.object.receiving)
            + "-"
            + str(remaining_per)
            + "-"
            + str(self.object.payment_days)
            + "Days"
        )
        self.object.user = self.request.user
        self.object.save()
        return super().form_valid(form)


class PaymentTermsUpdateView(
    HasPermissionsMixin,
    LoginRequiredMixin,
    PaymentTermsMenuMixin,
    SuccessMessageMixin,
    UpdateView,
):
    """Update Payment terms."""

    required_permission = "add_payment_terms"
    form_class = PaymentTermsForm
    model = PaymentTerms
    success_message = "Payment terms was created successfully"
    template_name = "setting/paymentterms/paymentterms_form.html"

    def form_valid(self, form):
        """If form is valid update title."""
        self.object = form.save(commit=False)
        deposit = Decimal(self.object.deposit)
        on_delivery = Decimal(self.object.on_delivery)
        receiving = Decimal(self.object.receiving)
        remaining_per = Decimal(100) - (deposit + on_delivery + receiving)
        self.object.remaining = remaining_per
        self.object.title = (
            "PAY"
            + str(self.object.deposit)
            + "-"
            + str(self.object.on_delivery)
            + "-"
            + str(self.object.receiving)
            + "-"
            + str(remaining_per)
            + "-"
            + str(self.object.payment_days)
            + "Days"
        )
        self.object.user = self.request.user
        self.object.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        return context


class PaymentTermsDeleteView(
    HasPermissionsMixin,
    LoginRequiredMixin,
    PaymentTermsMenuMixin,
    DeleteMixin,
    DeleteView,
):
    """Delete Payment Term."""

    required_permission = "delete_payment_terms"
    model = PaymentTerms
    success_message = "%(title)s was deleted successfully"
    protected_error = "can't delete %(title)s because it is used\
     by other forms"
    template_name = "setting/paymentterms/paymentterms_confirm_delete.html"

    def get_success_url(self):
        """Forward to url after deleting Product Terms successfully."""
        return reverse_lazy("setting:paymentterms_list")

    def get_error_url(self):
        """Forward to url if there is error while deleting Product Terms."""
        return reverse_lazy("setting:paymentterms_list")
