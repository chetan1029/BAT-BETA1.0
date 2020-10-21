"""View class and functions for Company app."""

import ast
import logging
from decimal import Decimal

from bat.company.models import HsCode
from bat.core.mixins import HasPermissionsMixin
from bat.product.forms import ProductForm, ProductParentForm
from bat.product.models import Product, ProductParent
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
from reversion.views import RevisionMixin
from rolepermissions.checkers import has_permission

logger = logging.getLogger(__name__)
Invitation = get_invitation_model()
User = get_user_model()


# Create Mixins
class ProductMenuMixin:
    """Mixing For Order Dashboard Menu."""

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        context["active_menu"] = {
            "dashboard": "global",
            "menu1": "product-management",
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


# Product
class ProductDashboardView(LoginRequiredMixin, ProductMenuMixin, TemplateView):
    """View Class to show Product dashboard after login."""

    template_name = "product/product/product_dashboard.html"

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        context["active_menu"].update({"menu2": "dashboard"})
        return context


class ProductCreateView(
    HasPermissionsMixin,
    LoginRequiredMixin,
    ProductMenuMixin,
    SuccessMessageMixin,
    CreateView,
):
    """Create Payment terms."""

    required_permission = "add_product"
    form_class = ProductForm
    model = Product
    success_url = reverse_lazy("product:product_list")
    success_message = "Product was created successfully"
    template_name = "product/product/product_form.html"

    def form_valid(self, form):
        """If form is valid update title."""
        tags = ast.literal_eval(form.cleaned_data["tags"])
        form.cleaned_data["tags"] = tags
        object = form.save(commit=False)
        object.company = self.request.member.company
        hscode = object.hscode
        hscode, create = HsCode.objects.get_or_create(
            hscode=hscode, company=self.request.member.company
        )
        object.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        context["active_menu"].update({"menu2": "global"})
        return context


class ProductListView(
    HasPermissionsMixin,
    LoginRequiredMixin,
    ProductMenuMixin,
    RevisionMixin,
    ListView,
):
    """List all the Product."""

    required_permission = "view_product"
    model = Product
    template_name = "product/product/product_list.html"

    def get_queryset(self):
        """Override the basic query with company object."""
        queryset = super().get_queryset()
        return queryset.filter(
            company=self.request.member.company, is_component=False
        )

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        context["active_menu"].update({"menu2": "product"})
        return context


class ProductActiveListView(ProductListView):
    """List all Active Product."""

    def get_queryset(self):
        """Override the basic query with company object."""
        queryset = super().get_queryset()
        return queryset.filter(is_active=True)

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        context["page_type"] = "active"
        return context


class ProductArchivedListView(ProductListView):
    """List all archived Product."""

    def get_queryset(self):
        """Override the basic query with company object."""
        queryset = super().get_queryset()
        return queryset.filter(is_active=False)

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        context["page_type"] = "archived"
        return context


class ProductGenricDeleteView(
    LoginRequiredMixin, ProductMenuMixin, DeleteMixin, DeleteView
):
    """Delete Product Genric view."""

    model = Product
    success_message = "%(title)s was deleted successfully"
    protected_error = "can't delete %(title)s because it is used\
     by other forms"
    template_name = "product/product/product_confirm_delete.html"

    def get_queryset(self):
        """Override the basic query with company object."""
        queryset = super().get_queryset()
        return queryset.filter(company=self.request.member.company)

    def get_success_url(self):
        """Forward to url after deleting Product Terms successfully."""
        return reverse_lazy("product:product_list")

    def get_error_url(self):
        """Forward to url if there is error while deleting Product Terms."""
        return reverse_lazy("product:product_list")

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        context["active_menu"].update({"menu2": "product"})
        return context


class ProductDeleteView(ProductGenricDeleteView):
    """Delete Product."""

    def get(self, request, *args, **kwargs):
        """Forward to delete page without confirmation for archived."""
        if has_permission(self.request.member, "delete_product"):
            self.request.is_archived = False
            self.request.is_restored = False
            return super().get(request, *args, **kwargs)
        else:
            raise PermissionDenied


class ProductArchivedView(ProductGenricDeleteView):
    """Archived Product."""

    success_message = "%(title)s was archived successfully"

    def get(self, request, *args, **kwargs):
        """Forward to delete page without confirmation for archived."""
        self.request.is_restored = False
        if has_permission(
            self.request.member, "archived_product"
        ) or has_permission(self.request.member, "delete_product"):
            self.request.is_archived = True
            return self.post(request, *args, **kwargs)
        else:
            raise PermissionDenied


class ProductRestoreView(ProductGenricDeleteView):
    """Restore Product."""

    success_message = "%(title)s was activated successfully"

    def get(self, request, *args, **kwargs):
        """Forward to delete page without confirmation for activate."""
        self.request.is_archived = False
        if has_permission(
            self.request.member, "archived_product"
        ) or has_permission(self.request.member, "delete_product"):
            self.request.is_restored = True
            return self.post(request, *args, **kwargs)
        else:
            raise PermissionDenied


# Component
class ComponentCreateView(
    HasPermissionsMixin,
    LoginRequiredMixin,
    ProductMenuMixin,
    SuccessMessageMixin,
    CreateView,
):
    """Create Component."""

    required_permission = "add_product"
    form_class = ProductParentForm
    model = Product
    success_message = "Component was created successfully"
    success_url = reverse_lazy("product:component_list")
    template_name = "product/component/component_form.html"

    def form_valid(self, form):
        """If form is valid update title."""
        tags = ast.literal_eval(form.cleaned_data["tags"])
        form.cleaned_data["tags"] = tags
        object = form.save(commit=False)
        object.company = self.request.member.company
        object.is_component = True
        object.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        context["active_menu"].update({"menu2": "component"})
        return context


class ComponentListView(
    HasPermissionsMixin,
    LoginRequiredMixin,
    ProductMenuMixin,
    RevisionMixin,
    ListView,
):
    """List all the Components."""

    required_permission = "view_product"
    model = Product
    template_name = "product/component/component_list.html"

    def get_queryset(self):
        """Override the basic query with company object."""
        queryset = super().get_queryset()
        return queryset.filter(
            company=self.request.member.company, is_component=True
        )

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        context["active_menu"].update({"menu2": "component"})
        return context


class ComponentActiveListView(ComponentListView):
    """List all Active Components."""

    def get_queryset(self):
        """Override the basic query with company object."""
        queryset = super().get_queryset()
        return queryset.filter(is_active=True)

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        context["page_type"] = "active"
        return context


class ComponentArchivedListView(ComponentListView):
    """List all archived components."""

    def get_queryset(self):
        """Override the basic query with company object."""
        queryset = super().get_queryset()
        return queryset.filter(is_active=False)

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        context["page_type"] = "archived"
        return context


class ComponentGenricDeleteView(
    LoginRequiredMixin, ProductMenuMixin, DeleteMixin, DeleteView
):
    """Delete Component Genric view."""

    model = Product
    success_message = "%(title)s was deleted successfully"
    protected_error = "can't delete %(title)s because it is used\
     by other forms"
    template_name = "product/component/component_confirm_delete.html"

    def get_queryset(self):
        """Override the basic query with company object."""
        queryset = super().get_queryset()
        return queryset.filter(company=self.request.member.company)

    def get_success_url(self):
        """Forward to url after deleting Product Terms successfully."""
        return reverse_lazy("product:component_list")

    def get_error_url(self):
        """Forward to url if there is error while deleting Product Terms."""
        return reverse_lazy("product:component_list")

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        context["active_menu"].update({"menu2": "component"})
        return context


class ComponentDeleteView(ComponentGenricDeleteView):
    """Delete Component."""

    def get(self, request, *args, **kwargs):
        """Forward to delete page without confirmation for archived."""
        if has_permission(self.request.member, "delete_product"):
            self.request.is_archived = False
            self.request.is_restored = False
            return super().get(request, *args, **kwargs)
        else:
            raise PermissionDenied


class ComponentArchivedView(ComponentGenricDeleteView):
    """Archived Component."""

    success_message = "%(title)s was archived successfully"

    def get(self, request, *args, **kwargs):
        """Forward to delete page without confirmation for archived."""
        self.request.is_restored = False
        if has_permission(
            self.request.member, "archived_product"
        ) or has_permission(self.request.member, "delete_product"):
            self.request.is_archived = True
            return self.post(request, *args, **kwargs)
        else:
            raise PermissionDenied


class ComponentRestoreView(ComponentGenricDeleteView):
    """Restore Component."""

    success_message = "%(title)s was activated successfully"

    def get(self, request, *args, **kwargs):
        """Forward to delete page without confirmation for activate."""
        self.request.is_archived = False
        if has_permission(
            self.request.member, "archived_product"
        ) or has_permission(self.request.member, "delete_product"):
            self.request.is_restored = True
            return self.post(request, *args, **kwargs)
        else:
            raise PermissionDenied
