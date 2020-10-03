"""View class and functions for Company app."""

import logging
from decimal import Decimal

from bat.company.forms import AccountSetupForm, CompanyForm, MemberForm
from bat.company.models import Company, Member
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
class CompanyMenuMixin:
    """Mixing For Company Menu."""

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        context["active_menu"] = {
            "dashboard": "global",
            "menu1": "company",
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
class AccountSetupView(
    LoginRequiredMixin, CompanyMenuMixin, SuccessMessageMixin, CreateView
):
    """Create Account Setup."""

    form_class = AccountSetupForm
    model = Company
    success_message = "Account setup was updated successfully"
    template_name = "company/company/account-setup.html"

    def form_valid(self, form):
        """If form is valid update title."""
        self.object = form.save(commit=False)
        self.object.save()

        member, create = Member.objects.get_or_create(
            job_title="Admin",
            user=self.request.user,
            company=self.object,
            invited_by=self.request.user,
            is_admin=True,
            is_active=True,
        )
        self.request.user.extra_data["step"] = 2
        self.request.user.extra_data["step_detail"] = "account setup"
        self.request.user.save()
        return super().form_valid(form)

    def get_success_url(self):
        """Forward to url after deleting Product successfully."""
        return reverse_lazy("core:dashboard")
