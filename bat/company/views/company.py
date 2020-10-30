"""View class and functions for Company app."""

import logging
from collections import OrderedDict
from decimal import Decimal

from bat.company.forms import (AccountSetupForm, BankForm, CompanyForm,
                               CompanyPaymentTermsForm, CompanyUpdateForm,
                               HsCodeForm, LocationForm, MemberForm,
                               MemberUpdateForm, PackingBoxForm, TaxForm,
                               VendorInviteForm)
from bat.company.models import (Bank, Company, CompanyPaymentTerms, HsCode,
                                Location, Member, PackingBox, Tax)
from bat.company.serializers import CompanyPaymentTermsSerializer
from bat.company.utils import get_cbm
from bat.core.mixins import HasPermissionsMixin
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.db.models.deletion import ProtectedError
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  TemplateView, UpdateView)
from invitations.utils import get_invitation_model
from notifications.signals import notify
from rest_framework import viewsets
from reversion.views import RevisionMixin
from rolepermissions.checkers import has_permission
from rolepermissions.permissions import revoke_permission
from rolepermissions.roles import RolesManager, assign_role, clear_roles

logger = logging.getLogger(__name__)
Invitation = get_invitation_model()
User = get_user_model()

# Create Mixins
class CompanyMenuMixin:
    """Mixing For Company Menu."""

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        context["active_menu"] = {"dashboard": "global", "menu1": "company"}
        return context


class VendorMenuMixin:
    """Mixing For Order Dashboard Menu."""

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        context["active_menu"] = {
            "dashboard": "global",
            "menu1": "supply-chain",
            "menu2": "vendors",
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
            try:
                if self.request.is_archived:
                    obj.is_active = False
                    obj.save()
                elif self.request.is_restored:
                    obj.is_active = True
                    obj.save()
                else:
                    obj.delete()
            except AttributeError:
                obj.delete()
            messages.success(self.request, self.success_message % obj.__dict__)
            return HttpResponseRedirect(get_success_url)
        except ProtectedError:
            messages.warning(self.request, self.protected_error % obj.__dict__)
            return HttpResponseRedirect(get_error_url)


# Create your views here.
# Vendor
class VendorDashboardView(LoginRequiredMixin, VendorMenuMixin, TemplateView):
    """View Class to show Supply Chain dashboard after login."""

    template_name = "company/vendor/vendor_dashboard.html"

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        return context


class VendorInviteView(
    LoginRequiredMixin,
    SuccessMessageMixin,
    RevisionMixin,
    VendorMenuMixin,
    CreateView,
):
    """Invite Vendor."""

    form_class = VendorInviteForm
    model = Company
    success_message = _("Invitation was successfully sent.")
    template_name = "company/vendor/vendor_form.html"

    def form_valid(self, form):
        """If form is valid update title."""
        self.object = form.save(commit=False)
        email = form.cleaned_data["email"].lower()
        # User Detail
        first_name = form.cleaned_data["first_name"]
        last_name = form.cleaned_data["last_name"]
        job_title = form.cleaned_data["job_title"]
        user_detail = {
            "first_name": first_name,
            "last_name": last_name,
            "job_title": job_title,
        }
        # Company Detail
        vendor_type = form.cleaned_data["vendor_type"]
        vendor_name = form.cleaned_data["vendor_name"]
        member_id = self.request.session.get("member_id")
        member = Member.objects.get(pk=member_id)
        company_detail = {
            "company_id": member.company_id,
            "company_name": member.company.name,
            "vendor_name": vendor_name,
            "vendor_type": vendor_type,
        }
        role = "vendor_admin"
        role_obj = RolesManager.retrieve_role(role)
        user_roles = {
            "roles": [role],
            "perms": list(role_obj.permission_names_list()),
        }
        extra_data = {}
        extra_data["type"] = "Vendor Invitation"
        invite = Invitation.create(
            email,
            inviter=self.request.user,
            user_detail=user_detail,
            company_detail=company_detail,
            user_roles=user_roles,
            extra_data=extra_data,
        )
        invite.send_invitation(self.request)

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        """Forward to url after sending invitation successfully."""
        return reverse_lazy("company:vendor_dashboard")

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        return context
