import csv
import html

from bat.market.models import AmazonProduct
from bat.setting.utils import get_status

from bat.product.constants import (
    PRODUCT_STATUS_ACTIVE, PRODUCT_STATUS_INACTIVE, PRODUCT_PARENT_STATUS)


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
