from rest_framework import serializers

from bat.market.models import AmazonMarketplace, AmazonOrder, AmazonProduct, AmazonAccounts

from bat.serializersFields.serializers_fields import CountrySerializerField
from bat.product.serializers import ImageSerializer
from bat.serializersFields.serializers_fields import (
    TagField,
    StatusField,
    MoneySerializerField,
)
from bat.market import constants


class AmazonMarketplaceSerializer(serializers.ModelSerializer):
    country = CountrySerializerField(required=False)
    status = serializers.SerializerMethodField()

    class Meta:
        model = AmazonMarketplace
        fields = ("id", "name", "country", "marketplaceId", "region", "status", )

    def get_status(self, obj):
        company_id = self.context.get("company_id")
        user = self.context.get("user")
        accounts = AmazonAccounts.objects.filter(
            marketplace_id=obj.id, user_id=user.id, company_id=company_id)
        if accounts.exists():
            return constants.MARKETPLACE_STATUS_ACTIVE
        return constants.MARKETPLACE_STATUS_INACTIVE


class SingleAmazonProductSerializer(serializers.ModelSerializer):
    images = ImageSerializer(many=True, read_only=True, required=False)
    tags = TagField(required=False)
    status = StatusField()

    class Meta:
        model = AmazonProduct
        fields = ("id", "amazonaccounts", "images", "title",
                  "sku", "ean", "asin", "type",
                  "url", "tags", "bullet_points",
                  "description", "status",
                  "extra_data", "parent",
                  )


class AmazonProductSerializer(serializers.ModelSerializer):
    images = ImageSerializer(many=True, read_only=True, required=False)
    tags = TagField(required=False)
    status = StatusField()
    parent = SingleAmazonProductSerializer()

    class Meta:
        model = AmazonProduct
        fields = ("id", "amazonaccounts", "images", "title",
                  "sku", "ean", "asin", "type",
                  "url", "tags", "bullet_points", "description",
                  "status", "extra_data", "parent",
                  )


class AmazonOrderSerializer(serializers.ModelSerializer):
    status = StatusField()
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
        fields = ("id", "order_id", "order_seller_id", "purchase_date",
                  "payment_date", "shipment_date", "reporting_date", "replacement",
                  "status", "sales_channel", "buyer_email", "quantity",
                  "promotion_quantity", "business_order", "amount", "tax",
                  "shipping_price", "shipping_tax", "gift_wrap_price",
                  "gift_wrap_tax", "item_promotional_discount",
                  "ship_promotional_discount", "fba_fullfilment_amount",
                  "amazon_comission_amount", "manufacturing_amount",
                  "amazonaccounts", "extra_data",
                  )
