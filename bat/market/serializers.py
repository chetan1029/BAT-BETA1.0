from rest_framework import serializers

from bat.market import constants
from bat.market.models import (
    AmazonAccounts,
    AmazonCompany,
    AmazonMarketplace,
    AmazonOrder,
    AmazonProduct,
)
from bat.product.serializers import ImageSerializer
from bat.serializersFields.serializers_fields import (
    CountrySerializerField,
    MoneySerializerField,
    StatusField,
    TagField,
)


class AmazonMarketplaceSerializer(serializers.ModelSerializer):
    country = CountrySerializerField(required=False)
    status = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    email_verified = serializers.SerializerMethodField()
    amazoncompany_id = serializers.SerializerMethodField()

    class Meta:
        model = AmazonMarketplace
        fields = (
            "id",
            "name",
            "country",
            "marketplaceId",
            "region",
            "status",
            "sales_channel_name",
            "email",
            "email_verified",
            "amazoncompany_id",
        )
        read_only_fields = (
            "id",
            "name",
            "country",
            "marketplaceId",
            "region",
            "status",
            "sales_channel_name",
            "amazoncompany_id",
        )

    def get_status(self, obj):
        company_id = self.context.get("company_id")
        user = self.context["request"].user
        accounts = AmazonAccounts.objects.filter(
            marketplace_id=obj.id,
            user_id=user.id,
            company_id=company_id,
            is_active=True,
        )
        if accounts.exists():
            return constants.MARKETPLACE_STATUS_ACTIVE
        return constants.MARKETPLACE_STATUS_INACTIVE

    def get_email(self, obj):
        company_id = self.context.get("company_id")
        user = self.context["request"].user
        accounts = AmazonAccounts.objects.filter(
            marketplace_id=obj.id, user_id=user.id, company_id=company_id
        )
        if accounts.exists():
            accounts = accounts.first()
            if accounts.credentails.email:
                return accounts.credentails.email
        return ""

    def get_email_verified(self, obj):
        company_id = self.context.get("company_id")
        user = self.context["request"].user
        accounts = AmazonAccounts.objects.filter(
            marketplace_id=obj.id, user_id=user.id, company_id=company_id
        )
        status = False
        if accounts.exists():
            accounts = accounts.first()
            status = accounts.credentails.email_verified
        return status

    def get_amazoncompany_id(self, obj):
        company_id = self.context.get("company_id")
        user = self.context["request"].user
        account = AmazonAccounts.objects.filter(
            marketplace_id=obj.id,
            user_id=user.id,
            company_id=company_id,
            is_active=True,
        ).first()
        if account:
            amazoncompany = AmazonCompany.objects.filter(
                amazonaccounts_id=account.id
            ).first()
            if amazoncompany:
                return amazoncompany.id
        return None


class SingleAmazonProductSerializer(serializers.ModelSerializer):
    images = ImageSerializer(many=True, read_only=True, required=False)
    tags = TagField(required=False)
    status = StatusField()

    class Meta:
        model = AmazonProduct
        fields = (
            "id",
            "amazonaccounts",
            "images",
            "title",
            "sku",
            "ean",
            "asin",
            "type",
            "url",
            "tags",
            "bullet_points",
            "description",
            "status",
            "extra_data",
            "parent",
        )


class AmazonProductSerializer(serializers.ModelSerializer):
    images = ImageSerializer(many=True, read_only=True, required=False)
    tags = TagField(required=False)
    status = StatusField()
    parent = SingleAmazonProductSerializer()

    class Meta:
        model = AmazonProduct
        fields = (
            "id",
            "amazonaccounts",
            "images",
            "title",
            "sku",
            "ean",
            "asin",
            "type",
            "url",
            "tags",
            "bullet_points",
            "description",
            "status",
            "extra_data",
            "parent",
        )


class AmazonOrderSerializer(serializers.ModelSerializer):
    status = StatusField(choices=constants.AMAZON_ORDER_STATUS_CHOICE)
    amount = MoneySerializerField()
    tax = MoneySerializerField()
    shipping_price = MoneySerializerField()
    shipping_tax = MoneySerializerField()
    gift_wrap_price = MoneySerializerField()
    gift_wrap_tax = MoneySerializerField()
    item_promotional_discount = MoneySerializerField()
    ship_promotional_discount = MoneySerializerField()
    fba_fullfilment_amount = MoneySerializerField()
    amazon_comission_amount = MoneySerializerField()
    manufacturing_amount = MoneySerializerField()

    class Meta:
        model = AmazonOrder
        fields = (
            "id",
            "order_id",
            "order_seller_id",
            "purchase_date",
            "payment_date",
            "shipment_date",
            "reporting_date",
            "replacement",
            "status",
            "sales_channel",
            "buyer_email",
            "quantity",
            "promotion_quantity",
            "business_order",
            "amount",
            "tax",
            "shipping_price",
            "shipping_tax",
            "gift_wrap_price",
            "gift_wrap_tax",
            "item_promotional_discount",
            "ship_promotional_discount",
            "fba_fullfilment_amount",
            "amazon_comission_amount",
            "manufacturing_amount",
            "amazonaccounts",
            "extra_data",
        )


class AmazonCompanySerializer(serializers.ModelSerializer):
    """Amazon Company serializers."""

    country = CountrySerializerField(required=False)

    class Meta:
        model = AmazonCompany
        fields = (
            "id",
            "amazonaccounts",
            "address1",
            "address2",
            "zip",
            "city",
            "region",
            "country",
            "store_name",
            "name",
            "email",
            "phone_number",
            "organization_number",
            "vat_number",
            "extra_data",
        )
        read_only_fields = ("id", "extra_data")
