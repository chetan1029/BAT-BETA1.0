"""View class and functions for Company app."""

import logging
from collections import OrderedDict
from decimal import Decimal

from bat.company.forms import (
    AccountSetupForm,
    BankForm,
    CompanyForm,
    CompanyPaymentTermsForm,
    CompanyUpdateForm,
    HsCodeForm,
    LocationForm,
    MemberForm,
    MemberUpdateForm,
    PackingBoxForm,
    TaxForm,
    VendorInviteForm,
)
from bat.company.models import (
    Bank,
    Company,
    CompanyPaymentTerms,
    HsCode,
    Location,
    Member,
    PackingBox,
    Tax,
)
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
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)
from django_filters.rest_framework import DjangoFilterBackend
from invitations.utils import get_invitation_model
from notifications.signals import notify
from rest_framework import filters, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from reversion.views import RevisionMixin
from rolepermissions.checkers import has_permission
from rolepermissions.permissions import revoke_permission
from rolepermissions.roles import RolesManager, assign_role, clear_roles

logger = logging.getLogger(__name__)
Invitation = get_invitation_model()
User = get_user_model()

# Create Mixins
class CompanySettingMenuMixin:
    """Mixing For Company Setting Menu."""

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        context["active_menu"] = {"dashboard": "global", "menu1": "setting"}
        return context


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
class AccountSetupView(
    LoginRequiredMixin, SuccessMessageMixin, RevisionMixin, CreateView
):
    """Create Account Setup."""

    form_class = AccountSetupForm
    model = Company
    success_message = "Account setup was updated successfully"
    template_name = "company/company/account_setup.html"

    def form_valid(self, form):
        """If form is valid update title."""
        self.object = form.save(commit=False)
        self.object.save()

        extra_data = {}
        extra_data["user_role"] = "company_admin"
        member, create = Member.objects.get_or_create(
            job_title="Admin",
            user=self.request.user,
            company=self.object,
            invited_by=self.request.user,
            is_admin=True,
            is_active=True,
            invitation_accepted=True,
            extra_data=extra_data,
        )
        # we have a signal that will allot that role to this user.
        self.request.user.extra_data["step"] = 2
        self.request.user.extra_data["step_detail"] = "account setup"
        self.request.user.save()
        return super().form_valid(form)

    def get_success_url(self):
        """Forward to url after deleting Product successfully."""
        return reverse_lazy("core:dashboard")


class CompanyProfileView(
    LoginRequiredMixin,
    CompanySettingMenuMixin,
    SuccessMessageMixin,
    RevisionMixin,
    UpdateView,
):
    """Create Account Setup."""

    form_class = CompanyUpdateForm
    model = Company
    success_url = reverse_lazy("company:company_profile")
    success_message = "Company Detail was updated successfully"
    template_name = "company/company/company_form.html"

    def form_valid(self, form):
        """Set Langauge of the submited form and set it as current."""
        return super().form_valid(form)

    def get_object(self):
        """
        User profile Update.

        UpdateView only allowed to use in view after passing pk in the url or
        pass it via get_object and we are passing currently loggedin user query
        via get_object.
        """
        member_id = self.request.session.get("member_id")
        company = Member.objects.get(pk=member_id).company
        return company

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        context["active_menu"].update({"menu2": "company-profile"})
        return context


# Member
class SettingsMemberListView(
    LoginRequiredMixin, CompanySettingMenuMixin, TemplateView
):
    """Company members view."""

    model = Member
    template_name = "company/member/member_list.html"

    def post(self, request, *args, **kwargs):
        """Post member id to this view."""
        context = self.get_context_data(**kwargs)
        type = request.POST.get("type", False)
        invitation_id = request.POST.get("invitation_id", False)
        if type == "invitation_resend":
            invitation = Invitation.objects.get(pk=invitation_id)
            invitation.send_invitation(self.request)
        elif type == "invitation_delete":
            Invitation.objects.filter(pk=invitation_id).delete()
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        context["active_menu"].update({"menu2": "members"})

        member_id = self.request.session.get("member_id")
        company = Member.objects.get(pk=member_id).company
        context["companyadmin_members"] = Member.objects.filter(
            company=company, is_active=True, is_admin=True
        )
        context["active_members"] = Member.objects.filter(
            company=company, is_active=True, is_admin=False
        )
        context["inactive_members"] = Member.objects.filter(
            company=company, is_active=False, invitation_accepted=True
        )
        context["pending_invitations"] = Invitation.objects.filter(
            accepted=False, company_detail__company_id=company.pk
        )
        return context


class SettingsMemberDetailView(
    LoginRequiredMixin, CompanySettingMenuMixin, UpdateView
):
    """Company Member detail page."""

    form_class = MemberUpdateForm
    model = Member
    success_url = reverse_lazy("company:settingsmember_list")
    success_message = "Profile was updated successfully."
    template_name = "company/member/member_detail.html"

    def form_valid(self, form):
        """If form is valid update title."""
        self.object = form.save(commit=False)
        self.object.save()
        # User Roles
        roles = form.cleaned_data.get("roles", "")
        roles = roles.split(",")

        perms = form.cleaned_data.get("permissions", "")
        perms = perms.split(",")

        if roles and perms:
            # Clear all old roles
            clear_roles(self.object)
            for role in roles:
                assign_role(self.object, role)
                role_obj = RolesManager.retrieve_role(role)
                # remove unneccesary permissions
                for perm in role_obj.permission_names_list():
                    if perm not in perms:
                        revoke_permission(self.object, perm)

        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        context["active_menu"].update({"menu2": "members"})
        all_roles = OrderedDict()
        for role in RolesManager.get_roles():
            role_name = role.get_name()
            all_roles[role_name] = {
                "display_name": "".join(
                    x.capitalize() + " " or "_" for x in role_name.split("_")
                ),
                "permissions": {
                    perm: "".join(
                        x.capitalize() + " " or "_" for x in perm.split("_")
                    )
                    for perm in role.permission_names_list()
                },
            }

        context["available_roles"] = all_roles
        return context


class SettingsMemberCreateView(
    LoginRequiredMixin,
    SuccessMessageMixin,
    RevisionMixin,
    CompanySettingMenuMixin,
    CreateView,
):
    """Invite staff member."""

    form_class = MemberForm
    model = Member
    success_message = _("Invitation was successfully sent.")
    template_name = "company/member/member_form.html"

    def get_initial(self):
        """Set initial value for the form field."""
        initial = super().get_initial()
        member_id = self.request.session.get("member_id")
        member = Member.objects.get(pk=member_id)
        initial["company_id"] = member.company_id
        return initial

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
        member_id = self.request.session.get("member_id")
        member = Member.objects.get(pk=member_id)
        company_detail = {
            "company_id": member.company_id,
            "company_name": member.company.name,
        }
        # User Roles
        roles = form.cleaned_data.get("roles", "")
        roles = roles.split(",")

        perms = form.cleaned_data.get("permissions", "")
        perms = perms.split(",")

        user_roles = {"roles": roles, "perms": perms}
        extra_data = {}
        extra_data["type"] = "Member Invitation"

        invite = Invitation.create(
            email,
            inviter=self.request.user,
            user_detail=user_detail,
            company_detail=company_detail,
            user_roles=user_roles,
            extra_data=extra_data,
        )
        invite.send_invitation(self.request)

        if User.objects.filter(email=email).exists():
            user = User.objects.filter(email=email).first()
            actions = [
                {
                    "href": reverse_lazy("accounts:my_companies"),
                    "title": _("View invitation"),
                }
            ]
            notify.send(
                self.request.user,
                recipient=user,
                verb=_("sent you an staff member invitation"),
                action_object=invite,
                target=member.company,
                description=_(
                    "{} has invited you to access {} as a staff \
                    member."
                ).format(self.request.user.username, member.company.name),
                actions=actions,
            )
            messages.success(self.request, self.success_message)
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        """Forward to url after deleting Product successfully."""
        return reverse_lazy("company:settingsmember_list")

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        context["active_menu"].update({"menu2": "members"})

        all_roles = OrderedDict()
        for role in RolesManager.get_roles():
            role_name = role.get_name()
            all_roles[role_name] = {
                "display_name": "".join(
                    x.capitalize() + " " or "_" for x in role_name.split("_")
                ),
                "permissions": {
                    perm: "".join(
                        x.capitalize() + " " or "_" for x in perm.split("_")
                    )
                    for perm in role.permission_names_list()
                },
            }

        context["available_roles"] = all_roles
        return context


# Company Filter backend.
class CompanyFilterBackend(filters.BaseFilterBackend):
    """Filter that only allows company to see their own objects."""

    def filter_queryset(self, request, queryset, view):
        """Override queryset with company filter."""
        return queryset.filter(company=request.member.company).order_by(
            "-create_date"
        )


# Company setting common viewset
class CompanySettingViewSet(viewsets.ModelViewSet):
    """List all the payment terms."""

    def perform_create(self, serializer):
        """Set the data for who is the owner or creater."""
        serializer.save(company=self.request.member.company)

    @action(detail=True, methods=["get"])
    def archived(self, request, *args, **kwargs):
        """Set the archived action."""
        object = self.get_object()
        object.is_active = False
        object.save()
        return Response({"status": self.archived_message})

    @action(detail=True, methods=["get"])
    def restore(self, request, *args, **kwargs):
        """Set the archived action."""
        object = self.get_object()
        object.is_active = True
        object.save()
        return Response({"status": self.restore_message})


# Payment terms
class SettingsPaymentTermsList(CompanySettingViewSet):
    """List all the payment terms."""

    serializer_class = CompanyPaymentTermsSerializer
    queryset = CompanyPaymentTerms.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        CompanyFilterBackend,
    ]
    filterset_fields = ["is_active", "payment_days"]
    search_fields = ["title"]

    archived_message = _("Paymentterms is archived")
    restore_message = _("Paymentterms is restored")


class SettingsPaymentTermsCreateView(
    HasPermissionsMixin,
    LoginRequiredMixin,
    CompanySettingMenuMixin,
    SuccessMessageMixin,
    CreateView,
):
    """Create Payment terms."""

    required_permission = "add_payment_terms"
    form_class = CompanyPaymentTermsForm
    model = CompanyPaymentTerms
    success_message = "Payment terms was created successfully"
    template_name = "company/paymentterms/paymentterms_form.html"

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
        self.object.company = self.request.member.company
        self.object.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        context["active_menu"].update({"menu2": "payment-terms"})
        return context


class SettingsPaymentTermsUpdateView(
    HasPermissionsMixin,
    LoginRequiredMixin,
    CompanySettingMenuMixin,
    SuccessMessageMixin,
    RevisionMixin,
    UpdateView,
):
    """Update Payment terms."""

    required_permission = "change_payment_terms"
    form_class = CompanyPaymentTermsForm
    model = CompanyPaymentTerms
    success_message = "Payment terms was created successfully"
    template_name = "company/paymentterms/paymentterms_form.html"

    def get_queryset(self):
        """Override the basic query with company object."""
        queryset = super().get_queryset()
        return queryset.filter(company=self.request.member.company)

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
        context["active_menu"].update({"menu2": "payment-terms"})
        return context


class SettingsPaymentTermsGenricDeleteView(
    LoginRequiredMixin, CompanySettingMenuMixin, DeleteMixin, DeleteView
):
    """Delete Payment Term."""

    model = CompanyPaymentTerms
    success_message = "%(title)s was deleted successfully"
    protected_error = "can't delete %(title)s because it is used\
     by other forms"
    template_name = "company/paymentterms/paymentterms_confirm_delete.html"

    def get_queryset(self):
        """Override the basic query with company object."""
        queryset = super().get_queryset()
        return queryset.filter(company=self.request.member.company)

    def get_success_url(self):
        """Forward to url after deleting Product Terms successfully."""
        return reverse_lazy("company:settingspaymentterms_list")

    def get_error_url(self):
        """Forward to url if there is error while deleting Product Terms."""
        return reverse_lazy("company:settingspaymentterms_list")

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        context["active_menu"].update({"menu2": "payment-terms"})
        return context


class SettingsPaymentTermsDeleteView(SettingsPaymentTermsGenricDeleteView):
    """Delete Payment Term."""

    def get(self, request, *args, **kwargs):
        """Forward to delete page without confirmation for archived."""
        if has_permission(self.request.member, "delete_payment_terms"):
            self.request.is_archived = False
            self.request.is_restored = False
            return super().get(request, *args, **kwargs)
        else:
            raise PermissionDenied


class SettingsPaymentTermsArchivedView(SettingsPaymentTermsGenricDeleteView):
    """Archived Payment Term."""

    success_message = "%(title)s was archived successfully"

    def get(self, request, *args, **kwargs):
        """Forward to delete page without confirmation for archived."""
        self.request.is_restored = False
        if has_permission(
            self.request.member, "archived_payment_terms"
        ) or has_permission(self.request.member, "delete_payment_terms"):
            self.request.is_archived = True
            return self.post(request, *args, **kwargs)
        else:
            raise PermissionDenied


class SettingsPaymentTermsRestoreView(SettingsPaymentTermsGenricDeleteView):
    """Restore Payment Term."""

    success_message = "%(title)s was activated successfully"

    def get(self, request, *args, **kwargs):
        """Forward to delete page without confirmation for activate."""
        self.request.is_archived = False
        if has_permission(
            self.request.member, "archived_payment_terms"
        ) or has_permission(self.request.member, "delete_payment_terms"):
            self.request.is_restored = True
            return self.post(request, *args, **kwargs)
        else:
            raise PermissionDenied


# Membership
class MembershipView(
    LoginRequiredMixin, CompanySettingMenuMixin, TemplateView
):
    """Membership view."""

    template_name = "company/membership/membership_detail.html"

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        context["active_menu"].update({"menu2": "membership"})
        return context


# Bank
class SettingsBankListView(
    HasPermissionsMixin,
    LoginRequiredMixin,
    CompanySettingMenuMixin,
    RevisionMixin,
    ListView,
):
    """List all the company banks."""

    required_permission = "view_company_banks"
    model = Bank
    template_name = "company/bank/bank_list.html"

    def get_queryset(self):
        """Override the basic query with company object."""
        queryset = super().get_queryset()
        return queryset.filter(company=self.request.member.company)

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        context["active_menu"].update({"menu2": "bank"})
        return context


class SettingsBankCreateView(
    HasPermissionsMixin,
    LoginRequiredMixin,
    CompanySettingMenuMixin,
    SuccessMessageMixin,
    CreateView,
):
    """Create Company Bank."""

    required_permission = "add_company_banks"
    form_class = BankForm
    model = Bank
    success_message = "Bank was created successfully"
    template_name = "company/bank/bank_form.html"

    def form_valid(self, form):
        """If form is valid update title."""
        self.object = form.save(commit=False)
        self.object.company = self.request.member.company
        self.object.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        context["active_menu"].update({"menu2": "bank"})
        return context


class SettingsBankDetailView(
    HasPermissionsMixin,
    LoginRequiredMixin,
    CompanySettingMenuMixin,
    DetailView,
):
    """Vendor bank detail page."""

    required_permission = "view_company_banks"
    model = Bank
    template_name = "company/bank/bank_detail.html"

    def get_queryset(self):
        """Override the basic query with company object."""
        queryset = super().get_queryset()
        return queryset.filter(company=self.request.member.company)

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        context["active_menu"].update({"menu2": "bank"})
        return context


class SettingsBankDeleteView(
    HasPermissionsMixin,
    LoginRequiredMixin,
    CompanySettingMenuMixin,
    DeleteMixin,
    DeleteView,
):
    """Delete Bank."""

    required_permission = "delete_company_banks"
    model = Bank
    success_message = "%(name)s was deleted successfully"
    protected_error = "can't delete %(name)s because it is used\
     by other forms"
    template_name = "company/bank/bank_confirm_delete.html"

    def get_queryset(self):
        """Override the basic query with company object."""
        queryset = super().get_queryset()
        return queryset.filter(company=self.request.member.company)

    def get_success_url(self):
        """Forward to url after deleting Product Terms successfully."""
        return reverse_lazy("company:settingsbank_list")

    def get_error_url(self):
        """Forward to url if there is error while deleting Product Terms."""
        return reverse_lazy("company:settingsbank_list")

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        context["active_menu"].update({"menu2": "bank"})
        return context


# Location
class SettingsLocationListView(
    HasPermissionsMixin,
    LoginRequiredMixin,
    CompanySettingMenuMixin,
    RevisionMixin,
    ListView,
):
    """List all the Locations."""

    required_permission = "view_company_locations"
    model = Location
    template_name = "company/location/location_list.html"

    def get_queryset(self):
        """Override the basic query with company object."""
        queryset = super().get_queryset()
        return queryset.filter(company=self.request.member.company)

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        context["active_menu"].update({"menu2": "location"})
        return context


class SettingsLocationCreateView(
    HasPermissionsMixin,
    LoginRequiredMixin,
    CompanySettingMenuMixin,
    SuccessMessageMixin,
    CreateView,
):
    """Create Location."""

    required_permission = "add_company_locations"
    form_class = LocationForm
    model = Location
    success_message = "Location was created successfully"
    template_name = "company/location/location_form.html"

    def form_valid(self, form):
        """If form is valid update title."""
        self.object = form.save(commit=False)
        self.object.company = self.request.member.company
        self.object.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        context["active_menu"].update({"menu2": "location"})
        return context


class SettingsLocationUpdateView(
    HasPermissionsMixin,
    LoginRequiredMixin,
    CompanySettingMenuMixin,
    SuccessMessageMixin,
    RevisionMixin,
    UpdateView,
):
    """Update Locations."""

    required_permission = "change_company_locations"
    form_class = LocationForm
    model = Location
    success_message = "Location was created successfully"
    template_name = "company/location/location_form.html"

    def get_queryset(self):
        """Override the basic query with company object."""
        queryset = super().get_queryset()
        return queryset.filter(company=self.request.member.company)

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        context["active_menu"].update({"menu2": "location"})
        return context


class SettingsLocationDeleteView(
    HasPermissionsMixin,
    LoginRequiredMixin,
    CompanySettingMenuMixin,
    DeleteMixin,
    DeleteView,
):
    """Delete Location."""

    required_permission = "delete_company_locations"
    model = Location
    success_message = "%(name)s was deleted successfully"
    protected_error = "can't delete %(name)s because it is used\
     by other forms"
    template_name = "company/location/location_confirm_delete.html"

    def get_queryset(self):
        """Override the basic query with company object."""
        queryset = super().get_queryset()
        return queryset.filter(company=self.request.member.company)

    def get_success_url(self):
        """Forward to url after deleting Product Terms successfully."""
        return reverse_lazy("company:settingslocation_list")

    def get_error_url(self):
        """Forward to url if there is error while deleting Product Terms."""
        return reverse_lazy("company:settingslocation_list")

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        context["active_menu"].update({"menu2": "location"})
        return context


# Packing Box
class SettingsPackingBoxListView(
    HasPermissionsMixin,
    LoginRequiredMixin,
    CompanySettingMenuMixin,
    RevisionMixin,
    ListView,
):
    """List all the Packing Box."""

    required_permission = "view_packing_box"
    model = PackingBox
    template_name = "company/packingbox/packingbox_list.html"

    def get_queryset(self):
        """Override the basic query with company object."""
        queryset = super().get_queryset()
        return queryset.filter(company=self.request.member.company)

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        context["active_menu"].update({"menu2": "packingbox"})
        return context


class SettingsPackingBoxCreateView(
    HasPermissionsMixin,
    LoginRequiredMixin,
    CompanySettingMenuMixin,
    SuccessMessageMixin,
    CreateView,
):
    """Create Packing Box."""

    required_permission = "add_packing_box"
    form_class = PackingBoxForm
    model = PackingBox
    success_message = "Packing Box was created successfully"
    template_name = "company/packingbox/packingbox_form.html"

    def form_valid(self, form):
        """If form is valid update title."""
        self.object = form.save(commit=False)
        self.object.company = self.request.member.company
        self.object.cbm = get_cbm(
            self.object.length,
            self.object.width,
            self.object.depth,
            self.object.length_unit,
        )
        self.object.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        context["active_menu"].update({"menu2": "packingbox"})
        return context


class SettingsPackingBoxUpdateView(
    HasPermissionsMixin,
    LoginRequiredMixin,
    CompanySettingMenuMixin,
    SuccessMessageMixin,
    RevisionMixin,
    UpdateView,
):
    """Update Packing Box."""

    required_permission = "change_packing_box"
    form_class = PackingBoxForm
    model = PackingBox
    success_message = "Packing Box was created successfully"
    template_name = "company/packingbox/packingbox_form.html"

    def get_queryset(self):
        """Override the basic query with company object."""
        queryset = super().get_queryset()
        return queryset.filter(company=self.request.member.company)

    def form_valid(self, form):
        """If form is valid update title."""
        self.object = form.save(commit=False)
        self.object.cbm = get_cbm(
            self.object.length,
            self.object.width,
            self.object.depth,
            self.object.length_unit,
        )
        self.object.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        context["active_menu"].update({"menu2": "packingbox"})
        return context


class SettingsPackingBoxDeleteView(
    HasPermissionsMixin,
    LoginRequiredMixin,
    CompanySettingMenuMixin,
    DeleteMixin,
    DeleteView,
):
    """Delete Packing Box."""

    required_permission = "delete_packing_box"
    model = PackingBox
    success_message = "%(name)s was deleted successfully"
    protected_error = "can't delete %(name)s because it is used\
     by other forms"
    template_name = "company/packingbox/packingbox_confirm_delete.html"

    def get_queryset(self):
        """Override the basic query with company object."""
        queryset = super().get_queryset()
        return queryset.filter(company=self.request.member.company)

    def get_success_url(self):
        """Forward to url after deleting Product Terms successfully."""
        return reverse_lazy("company:settingspackingbox_list")

    def get_error_url(self):
        """Forward to url if there is error while deleting Product Terms."""
        return reverse_lazy("company:settingspackingbox_list")

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        context["active_menu"].update({"menu2": "packingbox"})
        return context


# Hs Code
class SettingsHsCodeListView(
    HasPermissionsMixin,
    LoginRequiredMixin,
    CompanySettingMenuMixin,
    RevisionMixin,
    ListView,
):
    """List all the HS Code."""

    required_permission = "view_hscode"
    model = HsCode
    template_name = "company/hscode/hscode_list.html"

    def get_queryset(self):
        """Override the basic query with company object."""
        queryset = super().get_queryset()
        return queryset.filter(company=self.request.member.company)

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        context["active_menu"].update({"menu2": "hscode"})
        return context


class SettingsHsCodeCreateView(
    HasPermissionsMixin,
    LoginRequiredMixin,
    CompanySettingMenuMixin,
    SuccessMessageMixin,
    CreateView,
):
    """Create HS Code."""

    required_permission = "add_hscode"
    form_class = HsCodeForm
    model = HsCode
    success_message = "Packing Box was created successfully"
    template_name = "company/hscode/hscode_form.html"

    def form_valid(self, form):
        """If form is valid update title."""
        self.object = form.save(commit=False)
        self.object.company = self.request.member.company
        self.object.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        context["active_menu"].update({"menu2": "hscode"})
        return context


class SettingsHsCodeUpdateView(
    HasPermissionsMixin,
    LoginRequiredMixin,
    CompanySettingMenuMixin,
    SuccessMessageMixin,
    RevisionMixin,
    UpdateView,
):
    """Update HS Code."""

    required_permission = "change_hscode"
    form_class = HsCodeForm
    model = HsCode
    success_message = "Packing Box was created successfully"
    template_name = "company/hscode/hscode_form.html"

    def get_queryset(self):
        """Override the basic query with company object."""
        queryset = super().get_queryset()
        return queryset.filter(company=self.request.member.company)

    def form_valid(self, form):
        """If form is valid update title."""
        self.object = form.save(commit=False)
        self.object.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        context["active_menu"].update({"menu2": "hscode"})
        return context


class SettingsHsCodeDeleteView(
    HasPermissionsMixin,
    LoginRequiredMixin,
    CompanySettingMenuMixin,
    DeleteMixin,
    DeleteView,
):
    """Delete HS Code."""

    required_permission = "delete_hscode"
    model = HsCode
    success_message = "%(name)s was deleted successfully"
    protected_error = "can't delete %(name)s because it is used\
     by other forms"
    template_name = "company/hscode/hscode_confirm_delete.html"

    def get_queryset(self):
        """Override the basic query with company object."""
        queryset = super().get_queryset()
        return queryset.filter(company=self.request.member.company)

    def get_success_url(self):
        """Forward to url after deleting Product Terms successfully."""
        return reverse_lazy("company:settingshscode_list")

    def get_error_url(self):
        """Forward to url if there is error while deleting Product Terms."""
        return reverse_lazy("company:settingshscode_list")

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        context["active_menu"].update({"menu2": "hscode"})
        return context


# Taxes
class SettingsTaxListView(
    HasPermissionsMixin,
    LoginRequiredMixin,
    CompanySettingMenuMixin,
    RevisionMixin,
    ListView,
):
    """List all the Tax."""

    required_permission = "view_taxes"
    model = Tax
    template_name = "company/tax/tax_list.html"

    def get_queryset(self):
        """Override the basic query with company object."""
        queryset = super().get_queryset()
        return queryset.filter(company=self.request.member.company)

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        context["active_menu"].update({"menu2": "tax"})
        return context


class SettingsTaxCreateView(
    HasPermissionsMixin,
    LoginRequiredMixin,
    CompanySettingMenuMixin,
    SuccessMessageMixin,
    CreateView,
):
    """Create Tax."""

    required_permission = "add_taxes"
    form_class = TaxForm
    model = Tax
    success_message = "Tax was created successfully"
    template_name = "company/tax/tax_form.html"

    def form_valid(self, form):
        """If form is valid update title."""
        self.object = form.save(commit=False)
        self.object.company = self.request.member.company
        self.object.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        context["active_menu"].update({"menu2": "tax"})
        return context


class SettingsTaxUpdateView(
    HasPermissionsMixin,
    LoginRequiredMixin,
    CompanySettingMenuMixin,
    SuccessMessageMixin,
    RevisionMixin,
    UpdateView,
):
    """Update Tax."""

    required_permission = "change_taxes"
    form_class = TaxForm
    model = Tax
    success_message = "Packing Box was created successfully"
    template_name = "company/tax/tax_form.html"

    def get_queryset(self):
        """Override the basic query with company object."""
        queryset = super().get_queryset()
        return queryset.filter(company=self.request.member.company)

    def form_valid(self, form):
        """If form is valid update title."""
        self.object = form.save(commit=False)
        self.object.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        context["active_menu"].update({"menu2": "tax"})
        return context


class SettingsTaxDeleteView(
    HasPermissionsMixin,
    LoginRequiredMixin,
    CompanySettingMenuMixin,
    DeleteMixin,
    DeleteView,
):
    """Delete Tax."""

    required_permission = "delete_taxes"
    model = Tax
    success_message = "%(name)s was deleted successfully"
    protected_error = "can't delete %(name)s because it is used\
     by other forms"
    template_name = "company/tax/tax_confirm_delete.html"

    def get_queryset(self):
        """Override the basic query with company object."""
        queryset = super().get_queryset()
        return queryset.filter(company=self.request.member.company)

    def get_success_url(self):
        """Forward to url after deleting Product Terms successfully."""
        return reverse_lazy("company:settingstax_list")

    def get_error_url(self):
        """Forward to url if there is error while deleting Product Terms."""
        return reverse_lazy("company:settingstax_list")

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        context["active_menu"].update({"menu2": "tax"})
        return context
