import csv
import html

from djmoney.money import Money
from decimal import Decimal

from bat.market.models import AmazonProduct
from bat.setting.utils import get_status

from bat.product.constants import (
    PRODUCT_STATUS_ACTIVE,
    PRODUCT_STATUS_INACTIVE,
    PRODUCT_PARENT_STATUS,
)

from bat.market.constants import (
    ORDER_PARENT_STATUS,
    ORDER_STATUS_CANCELED,
    ORDER_STATUS_PENDING,
    ORDER_STATUS_SHIPPED,
)


class ReportAmazonProductCSVParser(object):

    @classmethod
    def parse(cls, csv_file):
        data = []
        product_status_active = get_status(
            PRODUCT_PARENT_STATUS, PRODUCT_STATUS_ACTIVE)
        product_status_inactive = get_status(
            PRODUCT_PARENT_STATUS, PRODUCT_STATUS_INACTIVE)
        product_status = {
            "Active": product_status_active,
            "Inactive": product_status_inactive
        }
        # read file
        reader = csv.DictReader(csv_file, delimiter='\t')

        for row in reader:
            ean = row.get("product-id", None)
            if ean:
                values = {}
                values["title"] = row.get("item-name", None)
                values["description"] = row.get("item-description", None)
                values["sku"] = html.unescape(row.get("seller-sku", None))
                values["asin"] = row.get("asin1", None)
                values["ean"] = row.get("product-id", None)
                values["status"] = product_status.get(row.get("status", None), None)
                values["url"] = "https://www.amazon.com/dp/" + row.get("asin1", None) + "/"
                data.append(values)
        return data, ["title", "description", "status", "url"]


class ReportAmazonOrdersCSVParser(object):

    @classmethod
    def parse(cls, orders_report_csv, orders_items_report_csv):

        def _get_item_data(row_data):
            item_price = row_data.get("item-price", None)
            item_tax = row_data.get("item-tax", None)
            shipping_price = row_data.get("shipping-price", None)
            shipping_tax = row_data.get("shipping-tax ", None)
            gift_wrap_price = row_data.get("gift-wrap-price", None)
            gift_wrap_tax = row_data.get("gift-wrap-tax", None)
            item_promotional_discount = row_data.get("item-promotion-discount", None)
            ship_promotional_discount = row_data.get("ship-promotion-discount", None)

            item_data = {
                "order_id": row_data.get("amazon-order-id"),
                "item_id": row_data.get("amazon-order-item-id"),
                "item_shipment_id": row_data.get("shipment-item-id"),
                "quantity": row_data.get("quantity-shipped"),
                "sku": row_data.get("sku"),
            }

            if item_price:
                item_data["item_price"] = Money(Decimal(item_price), row_data.get("currency"))
            if item_tax:
                item_data["item_tax"] = Money(Decimal(item_tax), row_data.get("currency"))
            if shipping_price:
                item_data["shipping_price"] = Money(
                    Decimal(shipping_price), row_data.get("currency"))
            if shipping_tax:
                item_data["shipping_tax"] = Money(Decimal(shipping_tax), row_data.get("currency"))
            if gift_wrap_price:
                item_data["gift_wrap_price"] = Money(
                    Decimal(gift_wrap_price), row_data.get("currency"))
            if gift_wrap_tax:
                item_data["gift_wrap_tax"] = Money(Decimal(gift_wrap_tax), row_data.get("currency"))
            if item_promotional_discount:
                item_data["item_promotional_discount"] = Money(
                    Decimal(item_promotional_discount), row_data.get("currency"))
            if ship_promotional_discount:
                item_data["ship_promotional_discount"] = Money(
                    Decimal(ship_promotional_discount), row_data.get("currency"))
            return item_data

        order_status_pending = get_status(
            ORDER_PARENT_STATUS, ORDER_STATUS_PENDING)
        order_status_shipped = get_status(
            ORDER_PARENT_STATUS, ORDER_STATUS_SHIPPED)
        order_status_canceled = get_status(
            ORDER_PARENT_STATUS, ORDER_STATUS_CANCELED)
        order_status = {
            "Pending": order_status_pending,
            "Shipped": order_status_shipped,
            "Canceled": order_status_canceled,
        }
        default_order_status = "Pending"

        # read files
        reader_orders = csv.DictReader(orders_report_csv, delimiter='\t')
        reader_items = csv.DictReader(orders_items_report_csv, delimiter='\t')

        order_status_map = {}
        order_items_map = {}

        for row in reader_orders:
            order_status_map[row["amazon-order-id"]] = row["order-status"]

        for row in reader_items:
            order = order_items_map.get(row.get("amazon-order-id"), None)
            if order:
                item_data = _get_item_data(row)
                if "item_price" in item_data:
                    if "amount" in order_items_map[row.get("amazon-order-id")]:
                        amount = order_items_map[row.get("amazon-order-id")]["amount"].amount + item_data.get(
                            "item_price").amount
                        order_items_map[row.get("amazon-order-id")
                                        ]["amount"] = Money(amount, row.get("currency", "USD"))

                if "item_tax" in item_data:
                    if "tax" in order_items_map[row.get("amazon-order-id")]:
                        tax = order_items_map[row.get("amazon-order-id")]["tax"].amount + item_data.get(
                            "item_tax").amount
                        order_items_map[row.get("amazon-order-id")
                                        ]["tax"] = Money(tax, row.get("currency", "USD"))

                if "shipping_price" in item_data:
                    if "shipping_price" in order_items_map[row.get("amazon-order-id")]:
                        shipping_price = order_items_map[row.get("amazon-order-id")]["shipping_price"].amount + item_data.get(
                            "shipping_price").amount
                        order_items_map[row.get("amazon-order-id")
                                        ]["shipping_price"] = Money(shipping_price, row.get("currency", "USD"))

                if "shipping_tax" in item_data:
                    if "shipping_tax" in order_items_map[row.get("amazon-order-id")]:
                        shipping_tax = order_items_map[row.get("amazon-order-id")]["shipping_tax"].amount + item_data.get(
                            "shipping_tax").amount
                        order_items_map[row.get("amazon-order-id")
                                        ]["shipping_tax"] = Money(shipping_tax, row.get("currency", "USD"))

                if "gift_wrap_price" in item_data:
                    if "gift_wrap_price" in order_items_map[row.get("amazon-order-id")]:
                        gift_wrap_price = order_items_map[row.get("amazon-order-id")]["gift_wrap_price"].amount + item_data.get(
                            "gift_wrap_price").amount
                        order_items_map[row.get("amazon-order-id")
                                        ]["gift_wrap_price"] = Money(gift_wrap_price, row.get("currency", "USD"))

                if "gift_wrap_tax" in item_data:
                    if "gift_wrap_tax" in order_items_map[row.get("amazon-order-id")]:
                        gift_wrap_tax = order_items_map[row.get("amazon-order-id")]["gift_wrap_tax"].amount + item_data.get(
                            "gift_wrap_tax").amount
                        order_items_map[row.get("amazon-order-id")
                                        ]["gift_wrap_tax"] = Money(gift_wrap_tax, row.get("currency", "USD"))

                if "item_promotional_discount" in item_data:
                    if "item_promotional_discount" in order_items_map[row.get("amazon-order-id")]:
                        item_promotional_discount = order_items_map[row.get("amazon-order-id")]["item_promotional_discount"].amount + item_data.get(
                            "item_promotional_discount").amount
                        order_items_map[row.get("amazon-order-id")
                                        ]["item_promotional_discount"] = Money(item_promotional_discount, row.get("currency", "USD"))

                if "ship_promotional_discount" in item_data:
                    if "ship_promotional_discount" in order_items_map[row.get("amazon-order-id")]:
                        ship_promotional_discount = order_items_map[row.get("amazon-order-id")]["ship_promotional_discount"].amount + item_data.get(
                            "ship_promotional_discount").amount
                        order_items_map[row.get("amazon-order-id")
                                        ]["ship_promotional_discount"] = Money(ship_promotional_discount, row.get("currency", "USD"))

                order_items_map[row.get("amazon-order-id")]["items"].append(item_data)
            else:
                values = {}
                values["order_id"] = row.get("amazon-order-id", None)
                values["order_seller_id"] = row.get("amazon-order-id ", None)
                values["purchase_date"] = row.get("purchase-date", None)
                values["payment_date"] = row.get("payments-date", None)
                values["shipment_date"] = row.get("shipment-date", None)
                values["reporting_date"] = row.get("reporting-date", None)
                values["buyer_email"] = row.get("buyer-email", None)
                values["sales_channel"] = row.get("sales-channel", None)
                values["status"] = order_status.get(
                    order_status_map.get(values["order_id"], default_order_status))

                item_data = _get_item_data(row)
                if "item_price" in item_data:
                    values["amount"] = Money(item_data.get(
                        "item_price").amount, row.get("currency", "USD"))

                if "item_tax" in item_data:
                    values["tax"] = Money(item_data.get("item_tax").amount,
                                          row.get("currency", "USD"))

                if "shipping_price" in item_data:
                    values["shipping_price"] = Money(item_data.get(
                        "shipping_price").amount, row.get("currency", "USD"))

                if "shipping_tax" in item_data:
                    values["shipping_tax"] = Money(item_data.get(
                        "shipping_tax").amount, row.get("currency", "USD"))

                if "gift_wrap_price" in item_data:
                    values["gift_wrap_price"] = Money(item_data.get(
                        "gift_wrap_price").amount, row.get("currency", "USD"))

                if "gift_wrap_tax" in item_data:
                    values["gift_wrap_tax"] = Money(item_data.get(
                        "gift_wrap_tax").amount, row.get("currency", "USD"))

                if "item_promotional_discount" in item_data:
                    values["item_promotional_discount"] = Money(item_data.get(
                        "item_promotional_discount").amount, row.get("currency", "USD"))

                if "ship_promotional_discount" in item_data:
                    values["ship_promotional_discount"] = Money(item_data.get(
                        "ship_promotional_discount").amount, row.get("currency", "USD"))

                values["items"] = [item_data]

                order_items_map[values["order_id"]] = values

        order_columns = ["order_seller_id", "purchase_date", "payment_date",
                         "shipment_date", "reporting_date", "buyer_email", "sales_channel",
                         "status", "amount", "tax", "shipping_price", "shipping_tax",
                         "gift_wrap_price", "item_promotional_discount", "ship_promotional_discount"]
        item_columns = ["item_id", "item_shipment_id", "quantity", "item_price", "item_tax", "shipping_price", "shipping_tax",
                        "gift_wrap_price", "item_promotional_discount", "ship_promotional_discount"]

        return list(order_items_map.values()), order_columns, item_columns
