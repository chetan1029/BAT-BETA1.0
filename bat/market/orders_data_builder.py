
from bat.market.models import AmazonOrder, AmazonOrderItem
from bat.setting.utils import get_status

from djmoney.money import Money
from decimal import Decimal

from bat.product.constants import (
    PRODUCT_STATUS_ACTIVE, PRODUCT_STATUS_INACTIVE, PRODUCT_PARENT_STATUS)


class AmazonOrderProcessData(object):

    @classmethod
    def builder(cls, response_data, amazon_account=None):
        data = []
        for row in response_data:
            values = {}
            if amazon_account:
                values["amazonaccounts"] = amazon_account
            values["order_id"] = row.get("AmazonOrderId", None)
            values["order_seller_id"] = row.get("SellerOrderId", None)
            values["purchase_date"] = row.get("PurchaseDate", None)
            values["payment_date"] = row.get("PurchaseDate", None)
            values["shipment_date"] = row.get("EarliestShipDate", None)
            values["reporting_date"] = row.get("LastUpdateDate", None)
            values["replacement"] = row.get("IsReplacementOrder", None)
            values["status"] = get_status(PRODUCT_PARENT_STATUS, row.get("OrderStatus", None))
            values["sales_channel"] = row.get("SalesChannel", None)
            values["quantity"] = row.get("NumberOfItemsShipped", None) + \
                row.get("NumberOfItemsUnshipped", None)

            order_total = row.get("OrderTotal", None)
            if order_total:
                values["amount"] = Money(Decimal(order_total.get(
                    "Amount")), order_total.get("CurrencyCode"))
            data.append(values)
        return data
