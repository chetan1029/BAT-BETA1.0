"""View class and functions for Company app."""

import ast
import logging

from bat.core.mixins import DeleteMixin, HasPermissionsMixin
from bat.product.forms import (
    ComponentForm,
    ComponentParentForm,
    ProductOptionForm,
)
from bat.product.models import (
    Product,
    ProductOption,
    ProductParent,
    ProductVariationOption,
)
from bat.setting.utils import get_status
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models.deletion import ProtectedError
from django.forms import formset_factory
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.text import slugify
from django.views.generic import CreateView, DeleteView, ListView
from invitations.utils import get_invitation_model
from measurement.measures import Weight
from reversion.views import RevisionMixin
from rolepermissions.checkers import has_permission

logger = logging.getLogger(__name__)
Invitation = get_invitation_model()
User = get_user_model()


# Create Mixins
class ComponentMenuMixin:
    """Mixing For Order Dashboard Menu."""

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        context["active_menu"] = {
            "dashboard": "global",
            "menu1": "product-management",
        }
        return context


# Component
class ComponentCreateView(
    HasPermissionsMixin,
    LoginRequiredMixin,
    ComponentMenuMixin,
    SuccessMessageMixin,
    CreateView,
):
    """Create Component."""

    required_permission = "add_product"
    form_class = ComponentParentForm
    model = ProductParent
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
        object.status = get_status("Product", "Inactive")
        object.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        context["active_menu"].update({"menu2": "component"})
        ProductOptionFormSet = formset_factory(
            ProductOptionForm, max_num=3, min_num=1
        )
        context["optionforms"] = ProductOptionFormSet(
            initial=[{"name": "Size"}]
        )
        return context


@transaction.atomic
def create_component(request):
    """Create Product function based view."""
    form = ComponentParentForm
    component_form = ComponentForm
    active_menu = {
        "dashboard": "global",
        "menu1": "product-management",
        "menu2": "component",
    }
    ProductOptionFormSet = formset_factory(
        ProductOptionForm, max_num=3, min_num=1
    )
    optionforms = ProductOptionFormSet(initial=[{"name": "Size"}])
    if request.method == "POST":
        form_valid = ComponentParentForm(request.POST)
        if form_valid.is_valid():
            is_variation = request.POST.get("is_variation", False)
            if is_variation:
                formset = ProductOptionFormSet(request.POST)
                if formset.is_valid():
                    # for formset_data in formset.cleaned_data:
                    #     logger.warning(formset_data["name"])
                    option1 = request.POST.get("option1", False)
                    option1_values = request.POST.get("option1_values", False)
                    option2 = request.POST.get("option2", False)
                    option2_values = request.POST.get("option2_values", False)
                    option3 = request.POST.get("option3", False)
                    option3_values = request.POST.get("option3_values", False)

                    if option1_values:
                        option1_values = option1_values.split(",")
                    if option2_values:
                        option2_values = option2_values.split(",")
                    if option3_values:
                        option3_values = option3_values.split(",")

                    message = ""
                    is_error = False
                    variation_options = []
                    for option1_value in option1_values:
                        option_data = {}
                        option_data["option1"] = option1
                        option_data["option1_value"] = option1_value

                        if not option2_values:
                            variation_id = slugify(str(option1_value))
                            variation_name = str(option1_value)
                            variation_available = request.POST.get(
                                "available" + variation_id, False
                            )
                            if variation_available:
                                model_number = request.POST.get(
                                    "model_number" + variation_id, False
                                )
                                if not model_number:
                                    message += (
                                        "Please enter model number for the variation "
                                        + str(variation_name)
                                        + "<br />"
                                    )
                                    is_error = True
                                manufacturer_part_number = request.POST.get(
                                    "manufacturer_part_number" + variation_id,
                                    False,
                                )
                                if not manufacturer_part_number:
                                    message += (
                                        "Please enter manufacturer part number for the variation "
                                        + str(variation_name)
                                        + "<br />"
                                    )
                                    is_error = True
                                weight = request.POST.get(
                                    "weight" + variation_id, False
                                )
                                weight_unit = request.POST.get(
                                    "weight_unit" + variation_id, False
                                )
                                option_data["model_number"] = model_number
                                option_data[
                                    "manufacturer_part_number"
                                ] = manufacturer_part_number
                                option_data["weight"] = weight
                                option_data["weight_unit"] = weight_unit
                                option_data["variation_name"] = variation_name
                                variation_options.append(option_data)

                        for option2_value in option2_values:
                            option_data = {}
                            option_data["option1"] = option1
                            option_data["option1_value"] = option1_value
                            option_data["option2"] = option2
                            option_data["option2_value"] = option2_value

                            if not option3_values:
                                variation_id = slugify(
                                    str(option1_value) + str(option2_value)
                                )
                                variation_name = (
                                    str(option1_value)
                                    + " "
                                    + str(option2_value)
                                )
                                variation_available = request.POST.get(
                                    "available" + variation_id, False
                                )
                                if variation_available:
                                    model_number = request.POST.get(
                                        "model_number" + variation_id, False
                                    )
                                    if not model_number:
                                        message += (
                                            "Please enter model number for the variation "
                                            + str(variation_name)
                                            + "<br />"
                                        )
                                        is_error = True
                                    manufacturer_part_number = request.POST.get(
                                        "manufacturer_part_number"
                                        + variation_id,
                                        False,
                                    )
                                    if not manufacturer_part_number:
                                        message += (
                                            "Please enter manufacturer part number for the variation "
                                            + str(variation_name)
                                            + "<br />"
                                        )
                                        is_error = True
                                    weight = request.POST.get(
                                        "weight" + variation_id, False
                                    )
                                    weight_unit = request.POST.get(
                                        "weight_unit" + variation_id, False
                                    )
                                    option_data["model_number"] = model_number
                                    option_data[
                                        "manufacturer_part_number"
                                    ] = manufacturer_part_number
                                    option_data["weight"] = weight
                                    option_data["weight_unit"] = weight_unit
                                    option_data[
                                        "variation_name"
                                    ] = variation_name
                                    variation_options.append(option_data)

                            for option3_value in option3_values:
                                option_data = {}
                                option_data["option1"] = option1
                                option_data["option1_value"] = option1_value
                                option_data["option2"] = option2
                                option_data["option2_value"] = option2_value
                                option_data["option3"] = option3
                                option_data["option3_value"] = option3_value
                                variation_id = slugify(
                                    str(option1_value)
                                    + str(option2_value)
                                    + str(option3_value)
                                )
                                variation_name = (
                                    str(option1_value)
                                    + " "
                                    + str(option2_value)
                                    + " "
                                    + str(option3_value)
                                )
                                variation_available = request.POST.get(
                                    "available" + variation_id, False
                                )
                                if variation_available:
                                    model_number = request.POST.get(
                                        "model_number" + variation_id, False
                                    )
                                    if not model_number:
                                        message += (
                                            "Please enter model number for the variation "
                                            + str(variation_name)
                                            + "<br />"
                                        )
                                        is_error = True
                                    manufacturer_part_number = request.POST.get(
                                        "manufacturer_part_number"
                                        + variation_id,
                                        False,
                                    )
                                    if not manufacturer_part_number:
                                        message += (
                                            "Please enter manufacturer part number for the variation "
                                            + str(variation_name)
                                            + "<br />"
                                        )
                                        is_error = True
                                    weight = request.POST.get(
                                        "weight" + variation_id, False
                                    )
                                    weight_unit = request.POST.get(
                                        "weight_unit" + variation_id, False
                                    )
                                    option_data["model_number"] = model_number
                                    option_data[
                                        "manufacturer_part_number"
                                    ] = manufacturer_part_number
                                    option_data["weight"] = weight
                                    option_data["weight_unit"] = weight_unit
                                    option_data[
                                        "variation_name"
                                    ] = variation_name
                                    variation_options.append(option_data)

                    if is_error:
                        data = {
                            "error": True,
                            "message": message,
                            "id": "messages",
                        }
                        return JsonResponse(data)
                    else:
                        tags = ast.literal_eval(
                            form_valid.cleaned_data["tags"]
                        )
                        form_valid.cleaned_data["tags"] = tags
                        component_parent = form_valid.save(commit=False)
                        component_parent.company = request.member.company
                        component_parent.is_component = True
                        component_parent.status = get_status(
                            "Product", "Active"
                        )
                        component_parent.save()
                        form_valid.save_m2m()

                        for variation in variation_options:
                            model_number = variation["model_number"]
                            manufacturer_part_number = variation[
                                "manufacturer_part_number"
                            ]
                            weight = variation["weight"]
                            weight_unit = variation["weight_unit"]

                            variation_name = variation["variation_name"]
                            title = (
                                str(component_parent.title)
                                + " "
                                + str(variation_name)
                            )

                            product = Product(
                                title=title,
                                model_number=model_number,
                                manufacturer_part_number=manufacturer_part_number,
                                is_active=True,
                                productparent=component_parent,
                                weight=Weight(**{weight_unit: weight}),
                            )
                            try:

                                product.validate_unique()
                                product.save()

                                productoption1, create = ProductOption.objects.get_or_create(
                                    name=variation["option1"],
                                    value=variation["option1_value"],
                                    productparent=component_parent,
                                )
                                productvariationoption = ProductVariationOption(
                                    product=product,
                                    productoption=productoption1,
                                )
                                productvariationoption.save()
                                try:
                                    productoption2, create = ProductOption.objects.get_or_create(
                                        name=variation["option2"],
                                        value=variation["option2_value"],
                                        productparent=component_parent,
                                    )
                                    productvariationoption = ProductVariationOption(
                                        product=product,
                                        productoption=productoption2,
                                    )
                                    productvariationoption.save()
                                    try:
                                        productoption3, create = ProductOption.objects.get_or_create(
                                            name=variation["option3"],
                                            value=variation["option3_value"],
                                            productparent=component_parent,
                                        )
                                        productvariationoption = ProductVariationOption(
                                            product=product,
                                            productoption=productoption3,
                                        )
                                        productvariationoption.save()
                                    except KeyError:
                                        pass
                                except KeyError:
                                    pass

                            except ValidationError as e:
                                if e:
                                    for error in e:
                                        message += str(error) + "<br />"
                                data = {
                                    "error": True,
                                    "message": message,
                                    "id": "messages",
                                }
                                transaction.set_rollback(True)
                                return JsonResponse(data)

                        data = {
                            "error": True,
                            "message": "Form Validated",
                            "id": "messages",
                        }
                        return JsonResponse(data)

                else:
                    message = ""
                    if formset.errors:
                        for field in formset:
                            for key, value in field.errors.items():
                                if key == "value":
                                    message += (
                                        "variation option values are required"
                                    )
                                if key == "name":
                                    message += (
                                        "variation option name is required"
                                    )
                    data = {
                        "error": True,
                        "message": message,
                        "id": "messages",
                    }
                    return JsonResponse(data)
            else:
                single_component_form = ComponentForm(request.POST)
                if single_component_form.is_valid():
                    tags = ast.literal_eval(form_valid.cleaned_data["tags"])
                    form_valid.cleaned_data["tags"] = tags
                    component_parent = form_valid.save(commit=False)
                    component_parent.company = request.member.company
                    component_parent.is_component = True
                    component_parent.status = get_status("Product", "Active")
                    component_parent.save()
                    form_valid.save_m2m()

                    title = component_parent.title
                    component_single = single_component_form.save(commit=False)
                    component_single.title = title
                    component_single.is_active = True
                    component_single.productparent = component_parent
                    component_single.save()

                    data = {
                        "error": True,
                        "message": "Single product",
                        "id": "messages",
                    }
                    return JsonResponse(data)
                else:
                    message = ""
                    if single_component_form.errors:
                        for field in single_component_form:
                            for error in field.errors:
                                message += (
                                    str(field.label)
                                    + ": "
                                    + str(error)
                                    + "<br />"
                                )
                    data = {
                        "error": True,
                        "message": message,
                        "id": "messages",
                    }
                    return JsonResponse(data)
        else:
            message = ""
            if form_valid.errors:
                for field in form_valid:
                    for error in field.errors:
                        message += (
                            str(field.label) + ": " + str(error) + "<br />"
                        )
            data = {"error": True, "message": message, "id": "messages"}
            return JsonResponse(data)
    return render(
        request,
        "product/component/component_form.html",
        {
            "form": form,
            "component_form": component_form,
            "active_menu": active_menu,
            "optionforms": optionforms,
        },
    )


class ComponentParentListView(
    HasPermissionsMixin,
    LoginRequiredMixin,
    ComponentMenuMixin,
    RevisionMixin,
    ListView,
):
    """List all the Components."""

    required_permission = "view_product"
    model = ProductParent
    template_name = "product/component/componentparent_list.html"

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


class ComponentParentActiveListView(ComponentParentListView):
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


class ComponentParentArchivedListView(ComponentParentListView):
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


class ComponentListView(
    HasPermissionsMixin,
    LoginRequiredMixin,
    ComponentMenuMixin,
    RevisionMixin,
    ListView,
):
    """List all the Child Components."""

    required_permission = "view_product"
    model = Product
    template_name = "product/component/component_list.html"

    def get_queryset(self):
        """Override the basic query with company object."""
        pk = self.kwargs["pk"]
        self.parentproduct = ProductParent.objects.get(pk=pk)
        queryset = super().get_queryset()
        return queryset.filter(
            productparent__company=self.request.member.company,
            productparent__is_component=True,
            productparent_id=pk,
        )

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        context["active_menu"].update({"menu2": "component"})
        context["parentproduct"] = self.parentproduct
        return context


class ComponentActiveListView(ComponentListView):
    """List all Active Child Components."""

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
    """List all archived child components."""

    def get_queryset(self):
        """Override the basic query with company object."""
        queryset = super().get_queryset()
        return queryset.filter(is_active=False)

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        context["page_type"] = "archived"
        return context


class ComponentParentGenricDeleteView(
    LoginRequiredMixin, ComponentMenuMixin, DeleteMixin, DeleteView
):
    """Delete Component Genric view."""

    model = ProductParent
    success_message = "%(title)s was deleted successfully"
    protected_error = "can't delete %(title)s because it is used\
     by other forms"
    template_name = "product/component/componentparent_confirm_delete.html"

    def get_queryset(self):
        """Override the basic query with company object."""
        queryset = super().get_queryset()
        return queryset.filter(company=self.request.member.company)

    def get_success_url(self):
        """Forward to url after deleting Product Terms successfully."""
        return reverse_lazy("product:componentparent_list")

    def get_error_url(self):
        """Forward to url if there is error while deleting Product Terms."""
        return reverse_lazy("product:componentparent_list")

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        context["active_menu"].update({"menu2": "component"})
        return context

    def delete(self, request, *args, **kwargs):
        """Delete method to define error messages."""
        obj = self.get_object()
        get_success_url = self.get_success_url()
        get_error_url = self.get_error_url()
        try:
            try:
                if self.request.is_archived:
                    obj.is_active = False
                    Product.objects.filter(productparent=obj).update(
                        is_active=False
                    )
                    obj.save()
                elif self.request.is_restored:
                    obj.is_active = True
                    Product.objects.filter(productparent=obj).update(
                        is_active=True
                    )
                    obj.save()
                else:
                    obj.delete()
                    Product.objects.filter(productparent=obj).delete()
            except AttributeError:
                obj.delete()
            messages.success(self.request, self.success_message % obj.__dict__)
            return HttpResponseRedirect(get_success_url)
        except ProtectedError:
            messages.warning(self.request, self.protected_error % obj.__dict__)
            return HttpResponseRedirect(get_error_url)


class ComponentParentDeleteView(ComponentParentGenricDeleteView):
    """Delete Component."""

    def get(self, request, *args, **kwargs):
        """Forward to delete page without confirmation for archived."""
        if has_permission(self.request.member, "delete_product"):
            self.request.is_archived = False
            self.request.is_restored = False
            return super().get(request, *args, **kwargs)
        else:
            raise PermissionDenied


class ComponentParentArchivedView(ComponentParentGenricDeleteView):
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


class ComponentParentRestoreView(ComponentParentGenricDeleteView):
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


class ComponentGenricDeleteView(
    LoginRequiredMixin, ComponentMenuMixin, DeleteMixin, DeleteView
):
    """Delete Component parent Genric view."""

    model = Product
    success_message = "%(title)s was deleted successfully"
    protected_error = "can't delete %(title)s because it is used\
     by other forms"
    template_name = "product/component/component_confirm_delete.html"

    def get_queryset(self):
        """Override the basic query with company object."""
        queryset = super().get_queryset()
        return queryset.filter(
            productparent__company=self.request.member.company
        )

    def get_success_url(self):
        """Forward to url after deleting Product Terms successfully."""
        product = Product.objects.get(pk=self.kwargs["pk"])
        return reverse_lazy(
            "product:component_list", kwargs={"pk": product.productparent_id}
        )

    def get_error_url(self):
        """Forward to url if there is error while deleting Product Terms."""
        product = Product.objects.get(pk=self.kwargs["pk"])
        return reverse_lazy(
            "product:component_list", kwargs={"pk": product.productparent_id}
        )

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        product = Product.objects.get(pk=self.kwargs["pk"])
        context["active_menu"].update({"menu2": "component"})
        context["product"] = product
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


def generate_variation(request):
    """Generate variation for product."""
    option1 = request.GET.get("option1")
    option2 = request.GET.get("option2")
    option3 = request.GET.get("option3")
    option1_values = request.GET.get("option1_values")
    option2_values = request.GET.get("option2_values")
    option3_values = request.GET.get("option3_values")

    if option1_values:
        option1_values = option1_values.split(",")
    if option2_values:
        option2_values = option2_values.split(",")
    if option3_values:
        option3_values = option3_values.split(",")

    variation_options = []
    for option1_value in option1_values:
        option_data = {}
        option_data["option1"] = option1
        option_data["option1_value"] = option1_value
        if not option2_values:
            variation_options.append(option_data)
        for option2_value in option2_values:
            option_data = {}
            option_data["option1"] = option1
            option_data["option1_value"] = option1_value
            option_data["option2"] = option2
            option_data["option2_value"] = option2_value
            if not option3_values:
                variation_options.append(option_data)
            for option3_value in option3_values:
                option_data = {}
                option_data["option1"] = option1
                option_data["option1_value"] = option1_value
                option_data["option2"] = option2
                option_data["option2_value"] = option2_value
                option_data["option3"] = option3
                option_data["option3_value"] = option3_value
                variation_options.append(option_data)
    return render(
        request,
        "product/product/ajax/variation.html",
        {
            "option1": option1,
            "option2": option2,
            "option3": option3,
            "option1_values": ",".join(option1_values),
            "option2_values": ",".join(option2_values),
            "option3_values": ",".join(option3_values),
            "variation_options": variation_options,
            "weight_unit": request.member.company.weight_unit,
        },
    )
