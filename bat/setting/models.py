"""Model classes for setting."""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import HStoreField
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from mptt.models import MPTTModel, TreeForeignKey

from bat.setting.constants import *

User = get_user_model()


class CategoryManager(models.Manager):
    def vendor_categories(self):
        return self.filter(is_vendor_category=True)


class Category(MPTTModel):
    """
    Category Model used for product, shipping, vendors etc.

    Here we can add categories in tree structure like parent->child relation.
    """

    name = models.CharField(max_length=200, verbose_name=_("Category Name"))
    rule = models.CharField(
        max_length=50, blank=True, null=True, verbose_name=_("Category Rule")
    )
    parent = TreeForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
    )
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    is_active = models.BooleanField(default=True)
    create_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(default=timezone.now)
    is_vendor_category = models.BooleanField(
        _("Is Vendor Category?"), default=False
    )
    extra_data = HStoreField(null=True, blank=True)

    objects = CategoryManager()

    class MPTTMeta:
        """Meta class for MPTT with some special functions."""

        order_insertion_by = ["name"]

    class Meta:
        """Meta Class."""

        unique_together = (("name", "parent"),)
        ordering = ["name"]
        verbose_name_plural = _("Categories")

    @property
    def full_path(self):
        """List of all categories."""
        full_path = [self.name]
        k = self.parent

        while k is not None:
            full_path.append(k.name)
            k = k.parent
        return full_path

    def category_breadcrumbs(self):
        """Category Breadcrumbs."""
        return " / ".join(self.full_path[::-1])

    def __str__(self):
        """Return Value."""
        return self.name


class Status(MPTTModel):
    """
    Status Model used for product, shipping, vendors etc.

    Here we can add status in parent->child relation.
    """

    name = models.CharField(max_length=200, verbose_name=_("Status Name"))
    parent = TreeForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
    )
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    is_active = models.BooleanField(default=True)
    create_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(default=timezone.now)

    class MPTTMeta:
        """Meta class for MPTT with some special functions."""

        order_insertion_by = ["name"]

    class Meta:
        """Meta Class."""

        unique_together = (("name", "parent"),)
        ordering = ["name"]
        verbose_name_plural = _("Statuses")

    @property
    def full_path(self):
        """List of all status."""
        full_path = [self.name]
        k = self.parent

        while k is not None:
            full_path.append(k.name)
            k = k.parent
        return full_path

    def status_breadcrumbs(self):
        """Status Breadcrumbs."""
        return " / ".join(self.full_path[::-1])

    def __str__(self):
        """Return Value."""
        return self.name


class PaymentTerms(models.Model):
    """
    Payment Terms Model.

    Model for Vendor Payment Terms.
    """

    title = models.CharField(
        max_length=200, unique=True, verbose_name=_("PaymentTerms Title")
    )
    deposit = models.DecimalField(
        max_digits=5, decimal_places=2, verbose_name=_("Deposit (in %)")
    )
    on_delivery = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name=_("Payment on delivery (in %)"),
    )
    receiving = models.DecimalField(
        max_digits=5, decimal_places=2, verbose_name=_("Receiving (in %)")
    )
    remaining = models.DecimalField(
        max_digits=5, decimal_places=2, verbose_name=_("Remaining (in %)")
    )
    payment_days = models.PositiveIntegerField(
        verbose_name=_("Payment Days (in days)")
    )
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    is_active = models.BooleanField(default=True)
    extra_data = HStoreField(null=True, blank=True)
    create_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(default=timezone.now)

    class Meta:
        """Meta Class."""

        verbose_name_plural = _("PaymentTerms")

    def __str__(self):
        """Return Value."""
        return self.title


class DeliveryTermName(models.Model):
    """
    Delivery Terms name Model.

    Model for Vendor Delivery Term name.
    """

    name = models.CharField(
        max_length=200, unique=True, verbose_name=_("Delivery Terms Title")
    )
    code = models.CharField(
        max_length=50, unique=True, verbose_name=_("Delivery Terms Code")
    )
    detail = models.TextField(blank=True)
    extra_data = HStoreField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        """Meta Class."""

        verbose_name_plural = _("Delivery Terms Name")

    def __str__(self):
        """Return Value."""
        return self.name


class DeliveryTerms(models.Model):
    """
    Delivery Terms Model.

    Model for Vendor Delivery Terms.
    """

    deliverytermname = models.ForeignKey(
        DeliveryTermName,
        on_delete=models.PROTECT,
        related_name="deliveryterms",
    )
    service_name = models.CharField(max_length=100)
    who_pays = models.CharField(
        max_length=20,
        choices=DELIVERY_WHO_PAYS,
        verbose_name=_("Who pays for the service"),
    )
    create_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(default=timezone.now)

    class Meta:
        """Meta Class."""

        verbose_name_plural = _("Delivery Terms")

    def __str__(self):
        """Return Value."""
        return (
            str(self.deliverytermname.name)
            + " - "
            + str(self.service_name)
            + " - Paid by "
            + str(self.who_pays)
        )
