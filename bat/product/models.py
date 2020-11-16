"""Model classes for product."""

from django.contrib.postgres.fields import HStoreField
from django.core.exceptions import ValidationError
from django.db import models
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django_measurement.models import MeasurementField
from measurement.measures import Weight
from rolepermissions.checkers import has_permission
from taggit.managers import TaggableManager

from bat.company.models import Company, Member
from bat.product.constants import *
from bat.setting.models import Status


def get_member_from_request(request):
    """
    get member from request bye resolving it
    """
    kwargs = request.resolver_match.kwargs
    company_pk = kwargs.get("company_pk", kwargs.get("pk", None))
    member = get_object_or_404(
        Member, company__id=company_pk, user=request.user.id
    )
    return member


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
    status = models.ForeignKey(Status, on_delete=models.PROTECT)
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

    @staticmethod
    def has_read_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "view_product")

    def has_object_read_permission(self, request):
        member = get_member_from_request(request)
        return has_permission(member, "view_product")

    @staticmethod
    def has_list_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "view_product")

    def has_object_list_permission(self, request):
        member = get_member_from_request(request)
        return has_permission(member, "view_product")

    @staticmethod
    def has_create_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "add_product")

    def has_object_create_permission(self, request):
        member = get_member_from_request(request)
        return has_permission(member, "add_product")

    @staticmethod
    def has_destroy_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "delete_product")

    def has_object_destroy_permission(self, request):
        member = get_member_from_request(request)
        return has_permission(member, "delete_product")

    @staticmethod
    def has_update_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "change_product")

    def has_object_update_permission(self, request):
        member = get_member_from_request(request)
        if not self.is_active:
            return False
        return has_permission(member, "change_product")

    @staticmethod
    def has_archive_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "archived_product")

    def has_object_archive_permission(self, request):
        member = get_member_from_request(request)
        return has_permission(member, "archived_product")

    @staticmethod
    def has_restore_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "restore_product")

    def has_object_restore_permission(self, request):
        member = get_member_from_request(request)
        return has_permission(member, "restore_product")


class Product(models.Model):
    """
    Product Model.

    We are using this model to store detail for both product and components.
    """

    productparent = models.ForeignKey(ProductParent, on_delete=models.CASCADE)
    title = models.CharField(verbose_name=_("Title"), max_length=500)
    sku = models.CharField(verbose_name=_("SKU"), max_length=200, blank=True)
    ean = models.CharField(verbose_name=_("EAN"), max_length=200, blank=True)
    model_number = models.CharField(
        max_length=200, blank=True, verbose_name=_("Model Number"), unique=True
    )
    manufacturer_part_number = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Manufacturer Part Number"),
        unique=True,
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

    def validate_unique(self, exclude=None):
        """Set unique Validation."""
        super(Product, self).validate_unique(exclude=exclude)
        errors = []
        if not self.id:
            if self.__class__.objects.filter(
                model_number=self.model_number
            ).exists():
                errors.append(
                    ValidationError(
                        _(
                            "Component %(name)s with same model number already exists"
                        ),
                        params={"name": self.title},
                    )
                )
            if self.__class__.objects.filter(
                manufacturer_part_number=self.manufacturer_part_number
            ).exists():
                errors.append(
                    ValidationError(
                        _(
                            "Component %(name)s with same manufacturer part number already exists"
                        ),
                        params={"name": self.title},
                    )
                )
            if errors:
                raise ValidationError(errors)

    def __str__(self):
        """Return Value."""
        return self.productparent.title

    @staticmethod
    def has_read_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "view_product")

    def has_object_read_permission(self, request):
        member = get_member_from_request(request)
        return has_permission(member, "view_product")

    @staticmethod
    def has_list_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "view_product")

    def has_object_list_permission(self, request):
        member = get_member_from_request(request)
        return has_permission(member, "view_product")

    @staticmethod
    def has_create_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "add_product")

    def has_object_create_permission(self, request):
        member = get_member_from_request(request)
        return has_permission(member, "add_product")

    @staticmethod
    def has_destroy_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "delete_product")

    def has_object_destroy_permission(self, request):
        member = get_member_from_request(request)
        return has_permission(member, "delete_product")

    @staticmethod
    def has_update_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "change_product")

    def has_object_update_permission(self, request):
        member = get_member_from_request(request)
        if not self.is_active:
            return False
        return has_permission(member, "change_product")

    @staticmethod
    def has_archive_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "archived_product")

    def has_object_archive_permission(self, request):
        member = get_member_from_request(request)
        return has_permission(member, "archived_product")

    @staticmethod
    def has_restore_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "restore_product")

    def has_object_restore_permission(self, request):
        member = get_member_from_request(request)
        return has_permission(member, "restore_product")


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
        return self.product.title + " - " + self.productoption.name
