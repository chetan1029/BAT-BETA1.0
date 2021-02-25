"""Model classes for product."""
import os
import uuid
import json
from decimal import Decimal


from bat.setting.utils import get_status
from bat.setting.models import Status
from bat.product.constants import *
from bat.company.models import Company, File, Member, PackingBox
from bat.company.models import Company, File, Member, PackingBox, HsCode
from django.core.exceptions import ValidationError as CoreValidationError
from taggit.models import Tag, TaggedItem
from taggit.managers import TaggableManager
from rolepermissions.checkers import has_permission
from rest_framework.exceptions import ValidationError
from measurement.measures import Weight
from djmoney.models.fields import MoneyField
from django_measurement.models import MeasurementField
from django_countries.fields import CountryField
from django.utils.translation import ugettext_lazy as _
from django.utils.text import slugify
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db import models, transaction


from django.contrib.contenttypes.fields import (
    GenericForeignKey,
    GenericRelation,
)
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import HStoreField


STATUS_DRAFT = 4


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


class IsDeletableMixin:
    def is_deletable(self):
        # get all the related object
        for rel in self._meta.get_fields():
            try:
                # check if there is a relationship with at least one related object
                if not rel.related_model.__name__ in self.ignore_rel_while_delete:
                    related = rel.related_model.objects.filter(**{rel.field.name: self})
                    if related.exists():
                        # if there is return a flag
                        return False
            except AttributeError:  # an attribute error for field occurs when checking for AutoField
                pass  # just pass as we dont need to check for AutoField
        return True


class ProductpermissionsModelmixin:
    @staticmethod
    def has_retrieve_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "view_product")

    def has_object_retrieve_permission(self, request):
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

    def delete(self, *args, **kwargs):
        self.image.delete(save=False)  # delete image
        super(Image, self).delete(*args, **kwargs)

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


class ProductManager(models.Manager):
    def import_bulk(self, data, columns, company):
        # get model_number map with map
        products_map_tuple = Product.objects.filter(
            company_id=company.id).values_list("model_number", "id")
        products_map = {k: v for k, v in products_map_tuple}

        # get exsisting hscoad map
        hscode_map_tuple = HsCode.objects.filter(company_id=company.id).values_list("hscode", "id")
        hscode_map = {k: v for k, v in hscode_map_tuple}

        # get exsisting tags map
        tags_map = {}
        if "tags" in columns:
            tags_map_tuple = Tag.objects.all().values_list("name", "id")
            tags_map = {k: v for k, v in tags_map_tuple}

        # grab invalid records
        invalid_records = []

        # create model objects
        product_tags_map = {}
        new_tags = []
        products_id = []
        products_update = []
        new_hscodes = []
        for row in data:
            if row.get("hscode", None):
                try:
                    if row["hscode"] != "":
                        _hscode_id = hscode_map[row["hscode"]]
                except KeyError as e:
                    new_hscodes.append(row["hscode"])
            values = row.copy()
            line_number = values.pop("line_number", None)
            # process on product object
            try:
                product_id = products_map[values.get("model_number", None)]
                products_id.append(product_id)
                if "tags" in columns:
                    tags = values.pop("tags", None)
                    if not tags is None:
                        tags = list(set(tags))
                        product_tags_map[product_id] = tags
                        for tag in tags:
                            try:
                                _t = tags_map[tag]
                            except KeyError as e:
                                new_tags.append(tag)

                product = Product(id=product_id, company=company, **values)
                try:
                    # validate object
                    product.full_clean(exclude=["id"])
                    products_update.append(product)
                except (CoreValidationError, ValidationError) as e:
                    # add validation error in file
                    if not line_number is None:
                        detail = {}
                        detail["id"] = str(product.id)
                        detail["line_number"] = line_number
                        detail["model_number"] = values.get("model_number", None)
                        detail["errors"] = json.dumps(e.message_dict)
                        invalid_records.append(detail)
                    else:
                        detail = {}
                        detail["id"] = str(product.id)
                        detail["model_number"] = values.get("model_number", None)
                        detail["errors"] = json.dumps(e.message_dict)
                        invalid_records.append(detail)
            except KeyError as e:
                # TODO create new objects
                pass

        try:
            # perform bulk operations
            with transaction.atomic():
                # hscode objects
                hscode_objs = []
                new_hscodes = list(set(new_hscodes))
                for hscode in new_hscodes:
                    hscode_objs.append(HsCode(company=company, hscode=hscode))
                HsCode.objects.bulk_create(hscode_objs)

                columns2 = columns.copy()
                columns2.remove("tags")
                Product.objects.bulk_update(products_update, columns2[:-1])

                if "tags" in columns:
                    # delete exsisting tagitems
                    ct = ContentType.objects.get(app_label='product', model='product')

                    TaggedItem.objects.filter(
                        content_type_id=ct.id, object_id__in=products_id).delete()

                    # create new objects
                    tag_objs = []
                    for tag in list(set(new_tags)):
                        tag_objs.append(Tag(name=tag, slug=slugify(tag, allow_unicode=True)))

                    Tag.objects.bulk_create(tag_objs)

                    # create tagitems objects
                    #   > get exsisting tags map
                    tags_map2 = {}
                    if "tags" in columns:
                        tags_map_tuple2 = Tag.objects.all().values_list("name", "id")
                        tags_map2 = {k: v for k, v in tags_map_tuple2}

                    #   > tagitem objects
                    tag_item_objs = []
                    for product_id, tags in product_tags_map.items():
                        for tag in tags:
                            tag_item_objs.append(TaggedItem(tag_id=tags_map2.get(
                                tag), object_id=product_id, content_type_id=ct.id))
                    TaggedItem.objects.bulk_create(tag_item_objs)
                return True, invalid_records
        except Exception as e:
            return False, invalid_records

    def bulk_delete(self, id_list):
        ids_cant_delete = []
        with transaction.atomic():
            products = Product.objects.filter(id__in=id_list)
            products_id = list(products.values_list("id", flat=True))
            for product in products:
                if not product.is_deletable():
                    products_id.remove(product.id)
                    ids_cant_delete.append(
                        {"id": product.id, "name": product.title})
            products = Product.objects.filter(id__in=products_id).delete()
        return ids_cant_delete

    def bulk_status_update(self, id_list, status):
        with transaction.atomic():
            status_obj = get_status(PRODUCT_PARENT_STATUS, PRODUCT_STATUS.get(status))
            Product.objects.filter(id__in=id_list).update(status=status_obj)


class Product(
    ProductpermissionsModelmixin, UniqueWithinCompanyMixin, IsDeletableMixin, models.Model
):
    """
    Product Model.

    We are using this model to store detail for both product and components.
    """

    company = models.ForeignKey(Company, on_delete=models.PROTECT)
    is_component = models.BooleanField(
        default=False, verbose_name=_("Is Component")
    )
    images = GenericRelation(Image)
    title = models.CharField(verbose_name=_("Title"), max_length=500)
    sku = models.CharField(verbose_name=_("SKU"), max_length=200, blank=True)
    ean = models.CharField(verbose_name=_("EAN"), max_length=200, blank=True)
    type = models.CharField(
        max_length=200, blank=True, verbose_name=_("Product Type")
    )
    series = models.CharField(
        max_length=200, blank=True, verbose_name=_("Product Series")
    )
    hscode = models.CharField(
        max_length=200, blank=True, verbose_name=_("Product HsCode")
    )
    tags = TaggableManager(blank=True)
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
    bullet_points = models.TextField(blank=True)
    description = models.TextField(blank=True)
    status = models.ForeignKey(Status, on_delete=models.PROTECT)
    extra_data = HStoreField(null=True, blank=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name="Select Parent",
        related_name="products",
    )
    create_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(default=timezone.now)

    objects = ProductManager()

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

    ignore_rel_while_delete = ["ProductVariationOption"]

    class Meta:
        """Meta Class."""

        verbose_name_plural = _("Products")

    @property
    def status_name(self):
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
        name = self.title
        if self.is_component:
            name += " - component"
        return name

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

    @staticmethod
    def has_bulk_action_permission(request):
        return True

    @staticmethod
    def has_import_bulk_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "add_product")


class ProductOption(models.Model):
    """
    Product Option Model.

    We are using this model to store product option like size, color, length
    etc.
    """

    company = models.ForeignKey(Company, on_delete=models.PROTECT)
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

        verbose_name_plural = _("Product Variation Options")

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
        Product, on_delete=models.CASCADE, related_name="product_rrps"
    )
    rrp = MoneyField(max_digits=14, decimal_places=2, default_currency="USD")
    country = CountryField()
    is_active = models.BooleanField(default=True)
    create_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(default=timezone.now)

    class Meta:
        """Meta Class."""

        verbose_name_plural = _("Product RRP's")
        unique_together = ["product", "country"]

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
    def has_csvexport_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "view_product")

    @staticmethod
    def has_xlsxeport_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "view_product")


class ProductPackingBox(ProductpermissionsModelmixin, models.Model):
    """
    Product Packing Box Model.

    Products packing boxes for shipment with quantity that can fit in the box.
    """

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="product_packingboxes"
    )
    packingbox = models.ForeignKey(
        PackingBox,
        on_delete=models.CASCADE,
        related_name="product_packingboxes",
    )
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


class ComponentMe(models.Model):
    """
    Component Manufacturer Expectation.

    Component manufacturer expectation for the component.
    """

    component = models.ForeignKey(Product, on_delete=models.CASCADE)
    version = models.DecimalField(max_digits=5, decimal_places=1)
    revision_history = models.TextField(blank=True)
    files = GenericRelation(File)
    status = models.ForeignKey(
        Status, on_delete=models.PROTECT, default=STATUS_DRAFT
    )
    is_active = models.BooleanField(default=False)
    create_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(default=timezone.now)

    class Meta:
        """Meta Class."""

        verbose_name_plural = _("Component MEs")

    def archive(self):
        """
        archive model instance
        """
        self.is_active = False
        self.save()
        for f in self.files.all():
            f.archive()

    def restore(self):
        """
        restore model instance
        """
        self.is_active = True
        self.save()
        for f in self.files.all():
            f.restore()

    def __str__(self):
        """Return Value."""
        return str(self.component.title) + " " + str(self.version)

    @staticmethod
    def has_retrieve_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "view_component_me")

    def has_object_retrieve_permission(self, request):
        member = get_member_from_request(request)
        return has_permission(member, "view_component_me")

    @staticmethod
    def has_list_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "view_component_me")

    def has_object_list_permission(self, request):
        member = get_member_from_request(request)
        return has_permission(member, "view_component_me")

    @staticmethod
    def has_create_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "add_component_me")

    def has_object_create_permission(self, request):
        member = get_member_from_request(request)
        return has_permission(member, "add_component_me")

    @staticmethod
    def has_destroy_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "delete_component_me")

    def has_object_destroy_permission(self, request):
        member = get_member_from_request(request)
        return has_permission(member, "delete_component_me")

    @staticmethod
    def has_update_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "change_component_me")

    def has_object_update_permission(self, request):
        member = get_member_from_request(request)
        if not self.is_active:
            return False
        return has_permission(member, "change_component_me")

    @staticmethod
    def has_archive_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "archived_component_me")

    def has_object_archive_permission(self, request):
        member = get_member_from_request(request)
        return has_permission(member, "archived_component_me")

    @staticmethod
    def has_restore_permission(request):
        member = get_member_from_request(request)
        return has_permission(member, "restore_component_me")

    def has_object_restore_permission(self, request):
        member = get_member_from_request(request)
        return has_permission(member, "restore_component_me")
