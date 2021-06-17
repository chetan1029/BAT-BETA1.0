import os
import uuid

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.postgres.fields import HStoreField
from django.db import models, transaction
from django.db.utils import IntegrityError
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from django_countries.fields import CountryField
from djmoney.models.fields import MoneyField
from taggit.managers import TaggableManager

from bat.company.models import Address, Company
from bat.globalprop.validator import validator
from bat.market.constants import AMAZON_REGIONS_CHOICES, EUROPE
from bat.product.models import Image, IsDeletableMixin
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

    name = models.CharField(verbose_name=_("Name"), max_length=512)
    country = CountryField(verbose_name=_("Country"))
    marketplaceId = models.CharField(
        verbose_name=_("MarketplaceId"), max_length=255
    )
    region = models.CharField(
        verbose_name=_("Region"),
        max_length=255,
        choices=AMAZON_REGIONS_CHOICES,
        default=EUROPE,
    )
    sales_channel_name = models.CharField(
        verbose_name=_("Sales Channel Name"), max_length=255
    )
    vat_tax_included = models.BooleanField(default=True)

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
    email = models.EmailField(
        max_length=100, verbose_name=_("Email"), blank=True
    )
    email_verified = models.BooleanField(default=False)
    region = models.CharField(
        verbose_name=_("Region"),
        max_length=255,
        choices=AMAZON_REGIONS_CHOICES,
        default=EUROPE,
    )

    def __str__(self):
        """Return Value."""
        return (
            self.selling_partner_id
            + " - "
            + self.user.username
            + " - "
            + self.region
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
    is_active = models.BooleanField(default=True)

    def __str__(self):
        """Return Value."""
        return (
            self.marketplace.name
            + " - "
            + self.marketplace.country.name
            + " - "
            + self.user.username
        )


class AmazonCompany(Address):
    """
    Amazon Company Model.

    Model to store information for companies as per marketplaces.
    """

    phone_validator = validator.phone_validator()
    amazonaccounts = models.OneToOneField(
        AmazonAccounts,
        on_delete=models.CASCADE,
        verbose_name="Select Amazon Account",
    )
    store_name = models.CharField(max_length=200, verbose_name=_("Store Name"))
    name = models.CharField(max_length=200, verbose_name=_("Name"))
    email = models.EmailField(max_length=100, verbose_name=_("Email"))
    phone_number = models.CharField(
        validators=[phone_validator],
        max_length=17,
        blank=True,
        verbose_name=_("Phone Number"),
    )
    organization_number = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Organization number"),
        help_text=_("Company register number for the marketplace company."),
    )
    vat_number = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("VAT number"),
        help_text=_("Company VAT number for the marketplace company."),
    )
    extra_data = HStoreField(null=True, blank=True)
    create_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(default=timezone.now)

    class Meta:
        """Meta Class."""

        verbose_name_plural = _("Amazon Companies")

    def __str__(self):
        """Return Value."""
        return str(self.id) + " - " + self.name


class UniqueWithinAmazonAccountMixin:
    def save(self, **kwargs):
        """
        To call clean method before save an instance of model.
        """
        self.clean()
        return super().save(**kwargs)

    def clean(self):
        """
        Validate field value should be unique within amazonaccount environment in a model.
        """
        errors = []
        for field_name in self.unique_within_amazonaccount:
            f = self._meta.get_field(field_name)
            lookup_value = getattr(self, f.attname)
            if lookup_value:
                kwargs = {
                    "amazonaccounts_id": self.amazonaccounts_id,
                    field_name: lookup_value,
                }
                if self.id:
                    if (
                        self.__class__.objects.filter(**kwargs)
                        .exclude(pk=self.id)
                        .exists()
                    ):
                        detail = {
                            field_name: self.velidation_within_amazonaccount_messages.get(
                                field_name, None
                            )
                        }
                        errors.append(detail)
                else:
                    if self.__class__.objects.filter(**kwargs).exists():
                        detail = {
                            field_name: self.velidation_within_amazonaccount_messages.get(
                                field_name, None
                            )
                        }
                        errors.append(detail)
        e = self.extra_clean()
        if len(e) > 0:
            errors.extend(e)
        if errors:
            raise ValidationError(errors)


class AmazonProductManager(models.Manager):
    def import_bulk(self, data, amazonaccount, columns):
        amazon_product_objects = []
        amazon_product_objects_update = []

        amazon_product_map_tuple = AmazonProduct.objects.filter(
            amazonaccounts_id=amazonaccount.id
        ).values_list("sku", "ean", "asin", "id")
        amazon_product_map = {
            k1 + k2 + k3: v for k1, k2, k3, v in amazon_product_map_tuple
        }

        for row in data:
            product_id = amazon_product_map.get(
                row.get("sku") + row.get("ean") + row.get("asin"), None
            )
            if product_id:
                amazon_product_objects_update.append(
                    AmazonProduct(
                        id=product_id, amazonaccounts=amazonaccount, **row
                    )
                )
            else:
                amazon_product_objects.append(
                    AmazonProduct(**row, amazonaccounts=amazonaccount)
                )
        with transaction.atomic():
            AmazonProduct.objects.bulk_create(amazon_product_objects)
            AmazonProduct.objects.bulk_update(
                amazon_product_objects_update, columns
            )


class AmazonProduct(
    UniqueWithinAmazonAccountMixin, IsDeletableMixin, models.Model
):
    """
    Amazon Product Model.

    Model for Amazon Product that use .
    """

    amazonaccounts = models.ForeignKey(
        AmazonAccounts,
        on_delete=models.CASCADE,
        verbose_name="Select Amazon Account",
    )
    thumbnail = models.CharField(
        verbose_name=_("Image url"), blank=True, max_length=1000
    )
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

    # UniqueWithinAmazonAccountMixin data
    unique_within_amazonaccount = ["sku", "ean", "asin"]
    velidation_within_amazonaccount_messages = {
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
    def import_bulk(self, data, amazonaccount, order_columns, item_columns):

        amazon_products = AmazonProduct.objects.filter(
            amazonaccounts_id=amazonaccount.id
        ).values_list("sku", "id")
        amazon_product_map = {k: v for k, v in amazon_products}

        amazon_orders = AmazonOrder.objects.filter(
            amazonaccounts_id=amazonaccount.id
        ).values_list("order_id", "id", "status__name")

        amazon_orders_map = {}
        amazon_orders_old_status_map = {}
        for order_id, pk, status in amazon_orders:
            amazon_orders_map[order_id] = pk
            amazon_orders_old_status_map[str(pk)] = status

        amazon_order_items = AmazonOrderItem.objects.filter(
            amazonorder__amazonaccounts_id=amazonaccount.id
        ).values_list("amazonorder_id", "item_id", "item_shipment_id", "id")
        amazon_order_items_map = {
            str(k1) + str(k2) + str(k3): v
            for k1, k2, k3, v in amazon_order_items
        }

        amazon_updated_orders_pk = []
        amazon_order_objects = []
        amazon_order_objects_update = []
        amazon_order_item_objects = []
        amazon_order_item_objects_update = []
        amazon_order_items = []
        for row in data:
            row_args = row.copy()
            amazon_order_items += row_args.pop("items", [])
            order_pk = amazon_orders_map.get(row.get("order_id"), None)

            if order_pk:
                amazon_order_objects_update.append(
                    AmazonOrder(
                        id=order_pk,
                        amazonaccounts_id=amazonaccount.id,
                        **row_args
                    )
                )
                amazon_updated_orders_pk.append(order_pk)
            else:
                amazon_order_objects.append(
                    AmazonOrder(amazonaccounts_id=amazonaccount.id, **row_args)
                )

        with transaction.atomic():
            AmazonOrder.objects.bulk_update(
                amazon_order_objects_update, order_columns + ["update_date"]
            )
            orders = AmazonOrder.objects.bulk_create(amazon_order_objects)

            amazon_new_order_map = {}
            amazon_created_orders_pk = []
            for order in orders:
                amazon_new_order_map[order.order_id] = order.id
                amazon_created_orders_pk.append(order.id)

            for order_item in amazon_order_items:
                sku = order_item.pop("sku", "")
                order_id = order_item.pop("order_id", "")
                order_item["amazonproduct_id"] = amazon_product_map.get(sku)
                order_item["amazonorder_id"] = amazon_new_order_map.get(
                    order_id, amazon_orders_map.get(order_id)
                )

                item_pk = amazon_order_items_map.get(
                    str(order_item["amazonorder_id"])
                    + str(order_item.get("item_id"))
                    + str(order_item.get("item_shipment_id")),
                    None,
                )
                if item_pk:
                    amazon_order_item_objects_update.append(
                        AmazonOrderItem(
                            id=item_pk, update_date=timezone.now, **order_item
                        )
                    )
                else:
                    amazon_order_item_objects.append(
                        AmazonOrderItem(**order_item)
                    )

            AmazonOrderItem.objects.bulk_update(
                amazon_order_item_objects_update, item_columns
            )
            AmazonOrderItem.objects.bulk_create(amazon_order_item_objects)

        return (
            amazon_created_orders_pk,
            amazon_updated_orders_pk,
            amazon_orders_old_status_map,
        )


class AmazonOrder(models.Model):
    """
    Order Model.

    Model for Orders.
    """

    order_id = models.CharField(max_length=300)
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
        max_digits=14,
        decimal_places=2,
        default_currency="USD",
        null=True,
        blank=True,
    )
    tax = MoneyField(
        max_digits=14,
        decimal_places=2,
        default_currency="USD",
        null=True,
        blank=True,
    )
    shipping_price = MoneyField(
        max_digits=14,
        decimal_places=2,
        default_currency="USD",
        null=True,
        blank=True,
    )
    shipping_tax = MoneyField(
        max_digits=14,
        decimal_places=2,
        default_currency="USD",
        null=True,
        blank=True,
    )
    gift_wrap_price = MoneyField(
        max_digits=14,
        decimal_places=2,
        default_currency="USD",
        null=True,
        blank=True,
    )
    gift_wrap_tax = MoneyField(
        max_digits=14,
        decimal_places=2,
        default_currency="USD",
        null=True,
        blank=True,
    )
    item_promotional_discount = MoneyField(
        max_digits=14,
        decimal_places=2,
        default_currency="USD",
        null=True,
        blank=True,
    )
    ship_promotional_discount = MoneyField(
        max_digits=14,
        decimal_places=2,
        default_currency="USD",
        null=True,
        blank=True,
    )
    fba_fullfilment_amount = MoneyField(
        max_digits=14,
        decimal_places=2,
        default_currency="USD",
        null=True,
        blank=True,
    )
    amazon_comission_amount = MoneyField(
        max_digits=14,
        decimal_places=2,
        default_currency="USD",
        null=True,
        blank=True,
    )
    manufacturing_amount = MoneyField(
        max_digits=14,
        decimal_places=2,
        default_currency="USD",
        null=True,
        blank=True,
    )
    amazonaccounts = models.ForeignKey(
        AmazonAccounts,
        on_delete=models.CASCADE,
        verbose_name="Select Amazon Account",
    )
    opt_out = models.BooleanField(default=False)
    amazon_review = models.BooleanField(default=False)
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
    item_shipment_id = models.CharField(max_length=300)
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
        max_digits=14,
        decimal_places=2,
        default_currency="USD",
        null=True,
        blank=True,
    )
    item_tax = MoneyField(
        max_digits=14,
        decimal_places=2,
        default_currency="USD",
        null=True,
        blank=True,
    )
    shipping_price = MoneyField(
        max_digits=14,
        decimal_places=2,
        default_currency="USD",
        null=True,
        blank=True,
    )
    shipping_tax = MoneyField(
        max_digits=14,
        decimal_places=2,
        default_currency="USD",
        null=True,
        blank=True,
    )
    gift_wrap_price = MoneyField(
        max_digits=14,
        decimal_places=2,
        default_currency="USD",
        null=True,
        blank=True,
    )
    gift_wrap_tax = MoneyField(
        max_digits=14,
        decimal_places=2,
        default_currency="USD",
        null=True,
        blank=True,
    )
    item_promotional_discount = MoneyField(
        max_digits=14,
        decimal_places=2,
        default_currency="USD",
        null=True,
        blank=True,
    )
    ship_promotional_discount = MoneyField(
        max_digits=14,
        decimal_places=2,
        default_currency="USD",
        null=True,
        blank=True,
    )
    fba_fullfilment_amount = MoneyField(
        max_digits=14,
        decimal_places=2,
        default_currency="USD",
        null=True,
        blank=True,
    )
    amazon_comission_amount = MoneyField(
        max_digits=14,
        decimal_places=2,
        default_currency="USD",
        null=True,
        blank=True,
    )
    manufacturing_amount = MoneyField(
        max_digits=14,
        decimal_places=2,
        default_currency="USD",
        null=True,
        blank=True,
    )
    item_return = models.PositiveIntegerField(default=0)
    extra_data = HStoreField(null=True, blank=True)
    create_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(default=timezone.now)

    class Meta:
        """Meta for the model."""

        unique_together = ("amazonorder", "item_id", "item_shipment_id")

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


class PPCCredentials(models.Model):
    """
    PPC - Credentials to hold up auth code, access token, refresh token, etc
    """

    auth_code = models.CharField(
        verbose_name="Auth Code", max_length=1024, blank=False, null=False
    )
    access_token = models.CharField(
        verbose_name="Access Token", max_length=2024, blank=False, null=False
    )
    refresh_token = models.CharField(
        verbose_name="Refresh Token", max_length=2024, blank=False, null=False
    )
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    create_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(default=timezone.now)

    class Meta:
        """Meta Class."""

        verbose_name_plural = _("PPC Credentials")

    def __str__(self):
        """Return Value."""
        return str(self.company.name)


class PPCProfileManager(models.Manager):
    def create_multiple_from_data(self, user, data):
        profiles = []
        for profileData in data:
            profile, created = self.update_or_create(
                profileId=profileData.get("profileId"),
                user=user,
                defaults=profileData,
            )
            profiles.append(profile)
        return profiles


class PPCProfile(models.Model):
    """
    PPC Profile
    """

    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    profile_id = models.BigIntegerField(
        _("Profile ID"), null=False, blank=False
    )
    amazonmarketplace = models.ForeignKey(
        AmazonMarketplace, on_delete=models.PROTECT
    )

    class Meta:
        """Meta Class."""

        verbose_name_plural = _("PPC Profile")

    def __str__(self):
        """Return Value."""
        return (
            str(self.company.name)
            + " - "
            + str(self.amazonmarketplace.country)
        )


class AmazonProductSessionsManager(models.Manager):
    def create_bulk(self, company_pk, data):
        amazon_products = AmazonProduct.objects.filter(
            amazonaccounts__company_id=company_pk
        ).values_list("sku", "id")
        amazon_product_map = {k: v for k, v in amazon_products}
        amazon_product_sessions = AmazonProductSessions.objects.filter(
            amazonproduct__amazonaccounts__company_id=company_pk
        ).values_list("amazonproduct_id", "date", "id")
        amazon_product_sessions_map = {
            str(k1) + str(k2): v for k1, k2, v in amazon_product_sessions
        }
        amazon_product_session_objs = []
        amazon_product_session_update_objs = []
        dublicate_data_mape = {}
        for row in data:
            row_data = row.copy()
            sku = row_data.pop("sku", None)
            amazon_product_id = amazon_product_map.get(sku, None)
            id_date = str(amazon_product_id) + str(row_data.get("date", None))
            if dublicate_data_mape.get(id_date, True):
                dublicate_data_mape[id_date] = False
                if amazon_product_id:
                    amazon_product_sessions_id = amazon_product_sessions_map.get(
                        id_date
                    )
                    if amazon_product_sessions_id:
                        amazon_product_session_update_objs.append(
                            AmazonProductSessions(
                                id=amazon_product_sessions_id,
                                amazonproduct_id=amazon_product_id,
                                **row_data
                            )
                        )
                    else:
                        amazon_product_session_objs.append(
                            AmazonProductSessions(
                                amazonproduct_id=amazon_product_id, **row_data
                            )
                        )
        try:
            with transaction.atomic():
                AmazonProductSessions.objects.bulk_create(
                    amazon_product_session_objs
                )
                AmazonProductSessions.objects.bulk_update(
                    amazon_product_session_update_objs,
                    [
                        "amazonproduct_id",
                        "date",
                        "sessions",
                        "page_views",
                        "conversion_rate",
                    ],
                )
                return True
        except IntegrityError as e:
            return False


class AmazonProductSessions(models.Model):
    """Amazon Product Sessions."""

    amazonproduct = models.ForeignKey(
        AmazonProduct,
        on_delete=models.CASCADE,
        verbose_name="Select Amazon Product",
    )
    sessions = models.PositiveIntegerField(default=0)
    page_views = models.PositiveIntegerField(default=0)
    conversion_rate = models.PositiveIntegerField(default=0)
    date = models.DateField(default=timezone.now)

    objects = AmazonProductSessionsManager()

    class Meta:
        """Product Keyword Meta."""

        unique_together = ("amazonproduct", "date")
        verbose_name_plural = _("Amazon Product Sessions")

    def __str__(self):
        """Return Value."""
        return str(self.amazonproduct.title)

    def save(self, *args, **kwargs):
        orders = AmazonOrderItem.objects.filter(
            amazonproduct=self.amazonproduct,
            amazonorder__purchase_date__date=self.date,
        ).count()
        conversion_rate = 0
        if orders and self.sessions:
            conversion_rate = round((orders / self.sessions) * 100)
        self.conversion_rate = conversion_rate
        return super().save(*args, **kwargs)
