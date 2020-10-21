"""Model classes for product."""
import os

from bat.company.models import Company, HsCode
from bat.setting.models import Status
from django.contrib.postgres.fields import HStoreField
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django_measurement.models import MeasurementField
from measurement.measures import Weight
from taggit.managers import TaggableManager

# Variables
CM = "cm"
IN = "in"
LENGTH_UNIT_TYPE = ((CM, "cm"), (IN, "in"))
STATUS_DEFAULT = "Active"

# Create your models here.
class ProductParent(models.Model):
    """
    Product Parent Model.

    We are using this model to store detail for the main product and all the
    other variation etc will be store in Product table with connection to
    ProductVariationOption.
    """

    company = models.ForeignKey(Company, on_delete=models.PROTECT)
    is_component = models.BooleanField(
        default=False, verbose_name=_("Is Component")
    )
    title = models.CharField(verbose_name=_("Title"), max_length=500)
    type = models.CharField(
        max_length=200, blank=True, verbose_name=_("Product Type")
    )
    series = models.CharField(
        max_length=200, blank=True, verbose_name=_("Product Series")
    )
    hscode = models.CharField(
        max_length=200, blank=True, verbose_name=_("Product HsCode")
    )
    sku = models.CharField(verbose_name=_("SKU"), max_length=200, blank=True)
    bullet_points = models.TextField(blank=True)
    description = models.TextField(blank=True)
    tags = TaggableManager(blank=True)
    is_active = models.BooleanField(default=True)
    status = models.ForeignKey(
        Status, on_delete=models.PROTECT, default=STATUS_DEFAULT
    )
    extra_data = HStoreField(null=True, blank=True)
    create_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(default=timezone.now)

    class Meta:
        """Meta Class."""

        verbose_name_plural = _("Products Parent")

    def get_absolute_url(self):
        """Set url of the page after adding/editing/deleting object."""
        # return reverse("vendor:vendor_detail", kwargs={"pk": self.pk})

    def __str__(self):
        """Return Value."""
        return self.title


class Product(models.Model):
    """
    Product Model.

    We are using this model to store detail for both product and components.
    """

    productparent = models.ForeignKey(ProductParent, on_delete=models.CASCADE)
    sku = models.CharField(verbose_name=_("SKU"), max_length=200, blank=True)
    ean = models.CharField(verbose_name=_("EAN"), max_length=200, blank=True)
    model_number = models.CharField(
        max_length=200, blank=True, verbose_name=_("Model Number")
    )
    manufacturer_part_number = models.CharField(
        max_length=200, blank=True, verbose_name=_("Manufacturer Part Number")
    )
    length = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name=_("Length"),
        blank=True,
        null=True,
    )
    width = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name=_("Width"),
        blank=True,
        null=True,
    )
    depth = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name=_("Depth"),
        blank=True,
        null=True,
    )
    length_unit = models.CharField(
        max_length=20,
        choices=LENGTH_UNIT_TYPE,
        default=CM,
        verbose_name=_("Length Unit"),
        blank=True,
    )
    weight = MeasurementField(
        measurement=Weight,
        unit_choices=(("g", "g"), ("kg", "kg"), ("oz", "oz"), ("lb", "lb")),
        blank=True,
        null=True,
    )
    is_active = models.BooleanField(default=True)
    extra_data = HStoreField(null=True, blank=True)
    create_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(default=timezone.now)

    class Meta:
        """Meta Class."""

        verbose_name_plural = _("Products")

    def get_absolute_url(self):
        """Set url of the page after adding/editing/deleting object."""
        # return reverse("vendor:vendor_detail", kwargs={"pk": self.pk})

    def __str__(self):
        """Return Value."""
        return self.productparent.title


class ProductOption(models.Model):
    """
    Product Option Model.

    We are using this model to store product option like size, color, length
    etc.
    """

    productparent = models.ForeignKey(ProductParent, on_delete=models.CASCADE)
    name = models.CharField(verbose_name=_("Option Name"), max_length=200)
    value = models.CharField(verbose_name=_("Option Value"), max_length=200)

    class Meta:
        """Meta Class."""

        verbose_name_plural = _("Product Options")

    def get_absolute_url(self):
        """Set url of the page after adding/editing/deleting object."""
        # return reverse("vendor:vendor_detail", kwargs={"pk": self.pk})

    def __str__(self):
        """Return Value."""
        return self.name


class ProductVariationOption(models.Model):
    """
    Product Variation Option Model.

    This table will connect product with their options like size, color etc.
    """

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    productoption = models.ForeignKey(ProductOption, on_delete=models.CASCADE)

    class Meta:
        """Meta Class."""

        verbose_name_plural = _("Product Options")

    def get_absolute_url(self):
        """Set url of the page after adding/editing/deleting object."""
        # return reverse("vendor:vendor_detail", kwargs={"pk": self.pk})

    def __str__(self):
        """Return Value."""
        return self.name
