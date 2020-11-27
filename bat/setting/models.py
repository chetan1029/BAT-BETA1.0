"""Model classes for setting."""

from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import HStoreField
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from mptt.models import MPTTModel, TreeForeignKey

User = get_user_model()


# Create your models here.
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
