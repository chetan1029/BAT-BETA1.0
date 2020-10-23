"""Froms related to Company app."""
import logging
from decimal import Decimal

from bat.product.lookups import (ProductHsCodeLookup, ProductOptionLookup,
                                 ProductSeriesLookup, ProductTagLookup,
                                 ProductTypeLookup)
from bat.product.models import Product, ProductOption, ProductParent
from bat.setting.models import Status
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Column, Layout, Row, Submit
from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from invitations.utils import get_invitation_model
from selectable.forms import (AutoComboboxSelectMultipleWidget,
                              AutoComboboxWidget,
                              AutoCompleteSelectMultipleWidget,
                              AutoCompleteWidget)

logger = logging.getLogger(__name__)
Invitation = get_invitation_model()


class ProductParentForm(forms.ModelForm):
    """Product Parent Form."""

    type_attrs = {
        "data-selectable-options": {"minLength": 0},
        "class": "form-control",
    }
    type = forms.CharField(
        widget=AutoComboboxWidget(
            lookup_class=ProductTypeLookup, allow_new=True, attrs=type_attrs
        )
    )

    series_attrs = {
        "data-selectable-options": {"minLength": 0},
        "class": "form-control",
    }
    series = forms.CharField(
        widget=AutoComboboxWidget(
            lookup_class=ProductSeriesLookup,
            allow_new=True,
            attrs=series_attrs,
        )
    )

    hscode_attrs = {
        "data-selectable-options": {"minLength": 0},
        "class": "form-control",
    }
    hscode = forms.CharField(
        widget=AutoComboboxWidget(
            lookup_class=ProductHsCodeLookup,
            allow_new=True,
            attrs=hscode_attrs,
        )
    )

    tags_attrs = {
        "data-selectable-options": {"minLength": 0},
        "class": "form-control",
    }
    tags = forms.CharField(
        widget=AutoComboboxSelectMultipleWidget(
            lookup_class=ProductTagLookup, attrs=tags_attrs
        ),
        required=False,
    )

    class Meta:
        """Defining Model and fields."""

        model = ProductParent
        fields = (
            "title",
            "sku",
            "type",
            "series",
            "hscode",
            "bullet_points",
            "description",
            "tags",
            "status",
        )

    def __init__(self, *args, **kwargs):
        """Init basic fields."""
        super().__init__(*args, **kwargs)
        self.fields["status"].queryset = Status.objects.filter(
            parent__name=settings.STATUS_PRODUCT
        )


class ComponentParentForm(ProductParentForm):
    """Form for Component Parent data."""

    def __init__(self, *args, **kwargs):
        """Init basic fields."""
        super().__init__(*args, **kwargs)
        self.fields["series"].required = False
        self.fields["hscode"].required = False
        self.fields["status"].required = False


class ProductForm(forms.ModelForm):
    """Product Form."""

    class Meta:
        """Defining Model and fields."""

        model = Product
        fields = (
            "sku",
            "ean",
            "model_number",
            "manufacturer_part_number",
            "length",
            "width",
            "depth",
            "length_unit",
            "weight",
        )

    def __init__(self, *args, **kwargs):
        """Init basic fields."""
        super().__init__(*args, **kwargs)
        self.fields["sku"].required = True
        self.fields["weight"].widget.attrs = {"class": "form-control"}

    def clean_sku(self, *args, **kwargs):
        """
        Perform validation on SKU.

        Fetch SKU field and perform validation like unique SKU in database
        or some other custom validation. you can raise error for perticular
        field from here that will be display as error on the formself.
        """
        sku = self.cleaned_data["sku"]
        if sku:
            if self.instance.id:
                if (
                    ProductParent.objects.filter(sku=sku)
                    .exclude(pk=self.instance.id)
                    .exists()
                ):
                    msg = _("Parent Component with same SKU already exists.")
                    raise forms.ValidationError(msg)
                return sku
            else:
                if ProductParent.objects.filter(sku=sku).exists():
                    msg = _("Parent Component with same SKU already exists.")
                    raise forms.ValidationError(msg)
                return sku


class ComponentForm(forms.ModelForm):
    """Component Form."""

    class Meta:
        """Defining Model and fields."""

        model = Product
        fields = ("model_number", "manufacturer_part_number", "weight")

    def __init__(self, *args, **kwargs):
        """Init basic fields."""
        super().__init__(*args, **kwargs)
        self.fields["model_number"].required = True
        self.fields["manufacturer_part_number"].required = True
        self.fields["weight"].widget.attrs = {"class": "form-control"}


class ProductOptionForm(forms.ModelForm):
    """Product Option Form."""

    name_attrs = {
        "data-selectable-options": {"minLength": 0},
        "class": "form-control",
    }
    name = forms.CharField(
        widget=AutoCompleteWidget(
            lookup_class=ProductOptionLookup, allow_new=True, attrs=name_attrs
        )
    )

    class Meta:
        """Defining Model and fields."""

        model = ProductOption
        fields = ("name", "value")

    def __init__(self, *args, **kwargs):
        """Init basic fields."""
        super().__init__(*args, **kwargs)
        self.fields["name"].widget.attrs = {"onChange": "generate_variation()"}
        self.fields["value"].widget.attrs = {"data-role": "tagsinput"}
