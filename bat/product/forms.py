"""Froms related to Company app."""
import logging
from decimal import Decimal

from bat.product.lookups import (ProductHsCodeLookup, ProductSeriesLookup,
                                 ProductTagLookup, ProductTypeLookup)
from bat.product.models import Product, ProductParent
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
        "onclick": "add_tags()",
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
        self.fields["weight"].widget.attrs = {"class": "form-control"}
