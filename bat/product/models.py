"""Model classes for product."""

import os
import uuid

from django.contrib.contenttypes.fields import (
    GenericForeignKey,
    GenericRelation,
)
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import HStoreField
from django.db import models
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django_countries.fields import CountryField
from django_measurement.models import MeasurementField
from djmoney.models.fields import MoneyField
from measurement.measures import Weight
from rest_framework.exceptions import ValidationError
from rolepermissions.checkers import has_permission
from taggit.managers import TaggableManager

from bat.company.models import Company, Member, PackingBox
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


class ProductpermissionsModelmixin:

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


class UniqueWithinCompanyMixin:
    def save(self, **kwargs):
        """
        To call clean method before save an instance of model.
        """
        self.clean()
        return super().save(**kwargs)

    def clean(self):
        """
        Validate field value should be unique within company environment in a model.
        """
        errors = []
        company = self.get_company
        company_path = self.get_company_path
        for field_name in self.unique_within_company:
            f = self._meta.get_field(field_name)
            lookup_value = getattr(self, f.attname)
            if lookup_value:
                kwargs = {company_path: company, field_name: lookup_value}
                if self.id:
                    if (
                        self.__class__.objects.filter(**kwargs)
                        .exclude(pk=self.id)
                        .exists()
                    ):
                        detail = {
                            field_name: self.velidation_within_company_messages.get(
                                field_name, None
                            )
                        }
                        errors.append(detail)
                else:
                    if self.__class__.objects.filter(**kwargs).exists():
                        detail = {
                            field_name: self.velidation_within_company_messages.get(
                                field_name, None
                            )
                        }
                        errors.append(detail)
        e = self.extra_clean()
        if len(e) > 0:
            errors.extend(e)
        if errors:
            raise ValidationError(errors)


def image_name(instance, filename):
    """Change name of image."""
    name, extension = os.path.splitext(filename)
    return "images/{0}_{1}/{2}_{3}{4}".format(
        instance.content_type.app_label,
        instance.content_type.model,
        str(name),
        uuid.uuid4(),
        extension,
    )


class Image(models.Model):
    """
    This table will store images that stored in AWS.
    """

    company = models.ForeignKey(Company, on_delete=models.PROTECT)
    image = models.ImageField(
        upload_to=image_name, blank=True, verbose_name=_("Image")
    )
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    main_image = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    create_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(default=timezone.now)

    # def delete(self, *args, **kwargs):
    #     print("\n\n inside delete \n\n ")
    #     super(Image, self).delete(*args, **kwargs)

    def archive(self):
        """
        archive model instance
        """
        self.is_active = False
        self.save()

    def restore(self):
        """
        restore model instance
        """
        self.is_active = True
        self.save()

    def __str__(self):
        """Return Value."""
        return self.image.name


class ProductParent(ProductpermissionsModelmixin, UniqueWithinCompanyMixin, models.Model):
    """
    Product Parent Model.

    We are using this model to store detail for the main product and all the
    other variation etc will be store in Product table with connection to
    ProductVariationOption.
    """

    company = models.ForeignKey(Company, on_delete=models.PROTECT)
    images = GenericRelation(Image)
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

    # UniqueWithinCompanyMixin data
    unique_within_company = ["sku"]
    velidation_within_company_messages = {
        "sku": _("Product Parent with same sku already exists.")
    }

    class Meta:
        """Meta Class."""

        verbose_name_plural = _("Products Parent")

    @property
    def get_status_name(self):
        """
        return status name
        """
        return self.status.name

    @property
    def get_company(self):
        """
        return related company
        """
        return self.company

    @property
    def get_company_path(self):
        """
        return related company
        """
        return "company"

    def extra_clean(self):
        """
        retuen list of model specific velidation errors or empty list
        """
        return []

    def archive(self):
        """
        archive model instance
        """
        self.is_active = False
        self.save()
        for image in self.images.all():
            image.archive()
        for product in self.products.all():
            product.archive()

    def restore(self):
        """
        restore model instance
        """
        self.is_active = True
        self.save()
        for image in self.images.all():
            image.restore()
        for product in self.products.all():
            product.restore()

    def __str__(self):
        """Return Value."""
        return self.title + " - " + str(self.id)

    @staticmethod
    def has_active_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "active_product")

    def has_object_active_permission(self, request):
        member = get_member_from_request(request)
        return has_permission(member, "active_product")


class Product(ProductpermissionsModelmixin, UniqueWithinCompanyMixin, models.Model):
    """
    Product Model.

    We are using this model to store detail for both product and components.
    """

    productparent = models.ForeignKey(
        ProductParent, on_delete=models.CASCADE, related_name="products"
    )
    images = GenericRelation(Image)
    title = models.CharField(verbose_name=_("Title"), max_length=500)
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

    # UniqueWithinCompanyMixin data
    unique_within_company = [
        "sku",
        "ean",
        "model_number",
        "manufacturer_part_number",
    ]
    velidation_within_company_messages = {
        "ean": _("Product with same ean already exists."),
        "sku": _("Product with same sku already exists."),
        "model_number": _("Product with same model_number already exists."),
        "manufacturer_part_number": _(
            "Product with same manufacturer_part_number already exists."
        ),
    }

    class Meta:
        """Meta Class."""

        verbose_name_plural = _("Products")

    @property
    def get_company(self):
        """
        return related company
        """
        return self.productparent.company

    @property
    def get_company_path(self):
        """
        return related company
        """
        return "productparent__company"

    def extra_clean(self):
        """
        retuen list of model specific velidation errors or empty list
        """
        errors = []
        if self.sku:
            if ProductParent.objects.filter(
                company=self.get_company, sku=self.sku
            ).exists():
                detail = {"sku": "Product Parent with this sku is exists."}
                errors.append(detail)
        return errors

    def archive(self):
        """
        archive model instance
        """
        self.is_active = False
        self.save()
        for image in self.images.all():
            image.archive()

        for product_component in self.productcomponents_product.all():
            product_component.archive()

        for product_rrp in self.product_rrps.all():
            product_rrp.archive()

    def restore(self):
        """
        restore model instance
        """
        self.is_active = True
        self.save()
        for image in self.images.all():
            image.restore()

        for product_component in self.productcomponents_product.all():
            product_component.restore()

        for product_rrp in self.product_rrps.all():
            product_rrp.restore()

    def __str__(self):
        """Return Value."""
        name = self.productparent.title + " - " + \
            str(self.productparent.id) + " - me -> " + str(self.id)
        if self.productparent.is_component:
            name += " - component"
        return name


class ProductOption(models.Model):
    """
    Product Option Model.

    We are using this model to store product option like size, color, length
    etc.
    """

    productparent = models.ForeignKey(
        ProductParent, on_delete=models.CASCADE, related_name="product_options"
    )
    name = models.CharField(verbose_name=_("Option Name"), max_length=200)
    value = models.CharField(verbose_name=_("Option Value"), max_length=200)

    class Meta:
        """Meta Class."""

        verbose_name_plural = _("Product Options")

    def __str__(self):
        """Return Value."""
        return self.name + " - " + self.value


class ProductVariationOption(models.Model):
    """
    Product Variation Option Model.

    This table will connect product with their options like size, color etc.
    """

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="product_variation_options",
    )
    productoption = models.ForeignKey(
        ProductOption, on_delete=models.CASCADE, related_name="product_options"
    )

    class Meta:
        """Meta Class."""

        verbose_name_plural = _("Product Options")

    def __str__(self):
        """Return Value."""
        return self.product.title + " - " + self.productoption.name


class ProductComponent(ProductpermissionsModelmixin, models.Model):
    """
    Product Component Model.

    We are using this model to connect product with its components.

    product and component must relate to the same company.
    product must not be marked as a component.
    component must be marked as a component.
    """

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="productcomponents_product",
    )
    component = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="productcomponents_component",
    )
    quantity = models.PositiveIntegerField(
        verbose_name=_("Quantity"), default=1
    )
    value = models.CharField(verbose_name=_("Option Value"), max_length=200)
    is_active = models.BooleanField(default=True)
    create_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(default=timezone.now)

    class Meta:
        """Meta Class."""

        verbose_name_plural = _("Product Components")

    def archive(self):
        """
        archive model instance
        """
        self.is_active = False
        self.save()

    def restore(self):
        """
        restore model instance
        """
        self.is_active = True
        self.save()

    def __str__(self):
        """Return Value."""
        return self.product.title


class ProductRrp(ProductpermissionsModelmixin, models.Model):
    """
    Product RRP Model.

    Products with their RRP's for different countries.
    product must not be marked as a component.
    """

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="product_rrps")
    rrp = MoneyField(max_digits=14, decimal_places=2, default_currency="USD")
    country = CountryField()
    is_active = models.BooleanField(default=True)
    create_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(default=timezone.now)

    class Meta:
        """Meta Class."""

        verbose_name_plural = _("Product RRP's")
        unique_together = ['product', 'country']

    def archive(self):
        """
        archive model instance
        """
        self.is_active = False
        self.save()

    def restore(self):
        """
        restore model instance
        """
        self.is_active = True
        self.save()

    def __str__(self):
        """Return Value."""
        return self.product.title

    
    @staticmethod
    def has_importfile_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "add_product")


class ProductPackingBox(ProductpermissionsModelmixin, models.Model):
    """
    Product Packing Box Model.

    Products packing boxes for shipment with quantity that can fit in the box.
    """

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="product_packingboxs")
    packingbox = models.ForeignKey(
        PackingBox, on_delete=models.CASCADE, related_name="product_packingboxs")
    weight = MeasurementField(
        measurement=Weight,
        unit_choices=(("g", "g"), ("kg", "kg"), ("oz", "oz"), ("lb", "lb")),
        blank=True,
        null=True,
    )
    units = models.PositiveIntegerField(
        verbose_name=_("Units per box"), default=1
    )
    is_active = models.BooleanField(default=True)
    create_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(default=timezone.now)

    class Meta:
        """Meta Class."""

        verbose_name_plural = _("Product Packing Boxes")

    def archive(self):
        """
        archive model instance
        """
        self.is_active = False
        self.save()

    def restore(self):
        """
        restore model instance
        """
        self.is_active = True
        self.save()

    def __str__(self):
        """Return Value."""
        return self.product.title
