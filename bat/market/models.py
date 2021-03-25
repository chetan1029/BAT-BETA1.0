import os
import uuid

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.postgres.fields import HStoreField
from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django_countries.fields import CountryField
from djmoney.models.fields import MoneyField
from taggit.managers import TaggableManager

from bat.company.models import Company
from bat.market.constants import AMAZON_REGIONS_CHOICES, EUROPE
from bat.product.models import Image, IsDeletableMixin, UniqueWithinCompanyMixin
from bat.setting.models import Status


User = get_user_model()


def file_name(instance, filename):
    """Change name of image."""
    name, extension = os.path.splitext(filename)
    return "files/marketplace/{0}_{1}{2}".format(
        str(name), uuid.uuid4(), extension
    )


class AmazonMarketplace(models.Model):
    """
    Amazon Marketplace Model.

    Model for Amazon Marketplace that use .
    """

    name = models.CharField(
        verbose_name=_("Name"), max_length=512, null=True, blank=True
    )
    country = CountryField(verbose_name=_("Country"))
    # TODO set countries_flag_url in CountryField for market icon
    marketplaceId = models.CharField(
        verbose_name=_("MarketplaceId"), max_length=255
    )
    region = models.CharField(
        verbose_name=_("Region"),
        max_length=255,
        choices=AMAZON_REGIONS_CHOICES,
        default=EUROPE,
    )

    def __str__(self):
        """Return Value."""
        return (
            self.region
            + " - "
            + self.country.name
            + " - "
            + self.marketplaceId
            + " - "
            + self.region
        )


class AmazonAccountCredentails(models.Model):
    """
    Amazon Accounts Credentail Model.

    Model for Amazon Accounts Credentail that use .
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    selling_partner_id = models.CharField(max_length=512, null=True)
    mws_auth_token = models.CharField(max_length=512, null=True)
    spapi_oauth_code = models.CharField(max_length=512, null=True)
    access_token = models.CharField(max_length=512, null=True)
    expires_at = models.DateTimeField(null=True)
    refresh_token = models.CharField(max_length=512, null=True)
    region = models.CharField(
        verbose_name=_("Region"),
        max_length=255,
        choices=AMAZON_REGIONS_CHOICES,
        default=EUROPE,
    )


class AmazonAccounts(models.Model):
    """
    Amazon Accounts Model.

    Model for Amazon Accounts that use .
    """

    marketplace = models.ForeignKey(
        AmazonMarketplace, on_delete=models.PROTECT
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    credentails = models.ForeignKey(
        AmazonAccountCredentails, on_delete=models.CASCADE, null=True
    )


class AmazonProductManager(models.Manager):
    def import_bulk(self, data, amazonaccount, columns):
        amazon_product_objects = []
        amazon_product_objects_update = []

        amazon_product_map_tuple = AmazonProduct.objects.filter(
            amazonaccounts_id=amazonaccount.id
        ).values_list("sku", "ean", "asin", "id")
        amazon_product_map = {k1 + k2 + k3: v for k1, k2, k3, v in amazon_product_map_tuple}

        for row in data:
            product_id = amazon_product_map.get(
                row.get("sku") + row.get("ean") + row.get("asin"), None)
            if product_id:
                amazon_product_objects_update.append(
                    AmazonProduct(id=product_id, amazonaccounts=amazonaccount, **row))
            else:
                amazon_product_objects.append(AmazonProduct(**row, amazonaccounts=amazonaccount))
        try:
            with transaction.atomic():
                AmazonProduct.objects.bulk_create(amazon_product_objects)
                AmazonProduct.objects.bulk_update(amazon_product_objects_update, columns)
        except Exception as e:
            return False
        return True


class AmazonProduct(UniqueWithinCompanyMixin, IsDeletableMixin, models.Model):
    """
    Amazon Product Model.

    Model for Amazon Product that use .
    """

    amazonaccounts = models.ForeignKey(
        AmazonAccounts,
        on_delete=models.CASCADE,
        verbose_name="Select Amazon Account",
    )
    images = GenericRelation(Image)
    title = models.CharField(verbose_name=_("Title"), max_length=500)
    sku = models.CharField(verbose_name="Seller SKU", max_length=200)
    ean = models.CharField(
        verbose_name="EAN", max_length=50, blank=True, default=""
    )
    asin = models.CharField(
        verbose_name="ASIN", max_length=50, default="", blank=True
    )
    type = models.CharField(
        max_length=200, blank=True, verbose_name=_("Product Type")
    )
    url = models.CharField(max_length=500, default="")
    tags = TaggableManager(blank=True)
    bullet_points = models.TextField(blank=True)
    description = models.TextField(blank=True)
    status = models.ForeignKey(
        Status,
        on_delete=models.PROTECT,
        verbose_name="Select Status",
        related_name="amazonproduct_status",
    )
    extra_data = HStoreField(null=True, blank=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        verbose_name="Select Parent",
        blank=True,
        null=True,
        related_name="products",
    )
    create_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(default=timezone.now)

    objects = AmazonProductManager()

    # UniqueWithinCompanyMixin data
    unique_within_company = ["sku", "ean", "asin"]
    velidation_within_company_messages = {
        "ean": _("Product with same EAN already exists."),
        "sku": _("Product with same SKU already exists."),
        "asin": _("Product with same ASIN already exists."),
    }

    def __str__(self):
        """Return Value."""
        return self.title

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
        return self.amazonaccounts.company

    @property
    def get_company_path(self):
        """
        return related company
        """
        return "amazonaccounts__company"

    def extra_clean(self):
        """
        retuen list of model specific velidation errors or empty list
        """
        return []


class AmazonOrdersManager(models.Manager):
    def create_bulk(self, data):
        amazon_order_objects = []

        for row in data:
            amazon_order_objects.append(AmazonOrder(**row))
        try:
            AmazonOrder.objects.bulk_create(amazon_order_objects)
        except Exception as e:
            return False
        return True


class AmazonOrder(models.Model):
    """
    Order Model.

    Model for Orders.
    """

    order_id = models.CharField(max_length=300, unique=True)
    order_seller_id = models.CharField(max_length=300, blank=True, null=True)
    purchase_date = models.DateTimeField()
    payment_date = models.DateTimeField(blank=True, null=True)
    shipment_date = models.DateTimeField(blank=True, null=True)
    reporting_date = models.DateTimeField(blank=True, null=True)
    replacement = models.CharField(max_length=10)
    status = models.ForeignKey(
        Status, on_delete=models.PROTECT, verbose_name="Select Status"
    )
    sales_channel = models.CharField(max_length=50)
    buyer_email = models.CharField(max_length=100, blank=True, null=True)
    quantity = models.PositiveIntegerField(blank=True, null=True)
    promotion_quantity = models.PositiveIntegerField(blank=True, null=True)
    business_order = models.CharField(
        max_length=10, blank=True, null=True, default="false"
    )
    amount = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD", null=True, blank=True
    )
    tax = MoneyField(max_digits=14, decimal_places=2, default_currency="USD", null=True, blank=True)
    shipping_price = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD", null=True, blank=True
    )
    shipping_tax = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD", null=True, blank=True
    )
    gift_wrap_price = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD", null=True, blank=True
    )
    gift_wrap_tax = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD", null=True, blank=True
    )
    item_promotional_discount = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD", null=True, blank=True
    )
    ship_promotional_discount = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD", null=True, blank=True
    )
    fba_fullfilment_amount = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD", null=True, blank=True
    )
    amazon_comission_amount = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD", null=True, blank=True
    )
    manufacturing_amount = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD", null=True, blank=True
    )
    amazonaccounts = models.ForeignKey(
        AmazonAccounts,
        on_delete=models.CASCADE,
        verbose_name="Select Amazon Account",
    )
    extra_data = HStoreField(null=True, blank=True)
    create_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(default=timezone.now)

    objects = AmazonOrdersManager()

    class Meta:
        """Meta for the model."""

        unique_together = ("amazonaccounts", "order_id")

    def __str__(self):
        """Return Value."""
        return str(self.order_id)


class AmazonOrderItem(models.Model):
    """
    Amazon Order Item Model.

    Model for Amazon Order Items.
    """

    amazonorder = models.ForeignKey(
        AmazonOrder,
        on_delete=models.CASCADE,
        verbose_name="Select Order",
        related_name="orderitem_order",
    )
    item_id = models.CharField(max_length=300)
    amazonproduct = models.ForeignKey(
        AmazonProduct,
        on_delete=models.CASCADE,
        verbose_name="Select Amazon Product",
        blank=True,
        null=True,
    )
    quantity = models.PositiveIntegerField(blank=True, null=True)
    asin = models.CharField(max_length=300, blank=True, null=True)
    item_price = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD"
    )
    item_tax = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD"
    )
    shipping_price = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD"
    )
    shipping_tax = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD"
    )
    gift_wrap_price = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD"
    )
    gift_wrap_tax = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD"
    )
    item_promotional_discount = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD"
    )
    ship_promotional_discount = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD"
    )
    fba_fullfilment_amount = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD"
    )
    amazon_comission_amount = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD"
    )
    manufacturing_amount = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD"
    )
    item_return = models.PositiveIntegerField(default=0)
    extra_data = HStoreField(null=True, blank=True)
    create_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(default=timezone.now)

    class Meta:
        """Meta for the model."""

        unique_together = ("amazonorder", "item_id")

    def __str__(self):
        """Return Value."""
        return str(self.item_id)


class AmazonOrderShipping(models.Model):
    """
    Order Shipping Model.

    Model for Order Shipping.
    """

    amazonorder = models.ForeignKey(
        AmazonOrder, on_delete=models.CASCADE, verbose_name="Select Order"
    )
    state = models.CharField(max_length=50, blank=True, null=True)
    city = models.CharField(max_length=50, blank=True, null=True)
    country = models.CharField(max_length=50, blank=True, null=True)
    postal_code = models.CharField(max_length=50, blank=True, null=True)
    extra_data = HStoreField(null=True, blank=True)
    create_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        """Return Value."""
        return str(self.amazonorder.order_id)
