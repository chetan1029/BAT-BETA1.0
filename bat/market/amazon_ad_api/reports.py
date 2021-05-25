# coding: utf-8
import gzip
import json

from .ad_client import AdClient
from .exception import ADAPIException

REPORT_TYPE = {
    "rp_scope": ["US1223366941512513", "CA4395156076169305"],
    "type": ["sp", "hsa"],
    "sp_keyword_seg": ["query", "placement"],
    "sp": ["campaigns", "adGroups", "keywords", "productAds", "targets"],
    "hsa": ["campaigns", "adGroups", "keywords"],
    "campaigns": [
        "portfolioId",
        "portfolioName",
        "bidPlus",
        "campaignStatus",
        "campaignBudget",
    ],
    "adGroups": ["adGroupName", "adGroupId"],
    "keywords": [
        "keywordId",
        "keywordText",
        "matchType",
        "adGroupName",
        "adGroupId",
    ],
    "productAds": ["adGroupName", "adGroupId", "currency", "asin", "sku"],
    "targets": [
        "targetId",
        "targetingExpression",
        "targetingText",
        "targetingType",
        "targetingType",
        "adGroupName",
        "adGroupId",
    ],
    "sp_common": [
        "campaignId",
        "campaignName",
        "impressions",
        "clicks",
        "cost",
        "attributedConversions1d",
        "attributedConversions7d",
        "attributedConversions14d",
        "attributedConversions30d",
        "attributedConversions1dSameSKU",
        "attributedConversions7dSameSKU",
        "attributedConversions14dSameSKU",
        "attributedConversions30dSameSKU",
        "attributedUnitsOrdered1d",
        "attributedUnitsOrdered7d",
        "attributedUnitsOrdered14d",
        "attributedUnitsOrdered30d",
        "attributedSales1d",
        "attributedSales7d",
        "attributedSales14d",
        "attributedSales30d",
        "attributedSales1dSameSKU",
        "attributedSales7dSameSKU",
        "attributedSales14dSameSKU",
        "attributedSales30dSameSKU",
        "attributedUnitsOrdered1dSameSKU",
        "attributedUnitsOrdered7dSameSKU",
        "attributedUnitsOrdered14dSameSKU",
        "attributedUnitsOrdered30dSameSKU",
    ],
    "hsa_common": [
        "campaignId",
        "campaignName",
        "impressions",
        "clicks",
        "cost",
        "attributedSales14d",
        "attributedSales14dSameSKU",
        "attributedConversions14d",
        "attributedConversions14dSameSKU",
        "attributedOrdersNewToBrand14d",
        "attributedOrdersNewToBrandPercentage14d",
        "attributedOrderRateNewToBrand14d",
        "attributedSalesNewToBrand14d",
        "attributedSalesNewToBrandPercentage14d",
        "attributedUnitsOrderedNewToBrand14d",
        "attributedUnitsOrderedNewToBrandPercentage14d",
    ],
    "asins": [
        "adGroupName",
        "adGroupId",
        "keywordId",
        "keywordText",
        "asin",
        "otherAsin",
        "currency",
        "matchType",
        "campaignName",
        "campaignId",
        "sku",
        "attributedUnitsOrdered7dOtherSKU",
        "attributedSales7dOtherSKU",
    ],
    "asins_for_seller": [
        "sku",
        "attributedUnitsOrdered1dOtherSKU",
        "attributedUnitsOrdered7dOtherSKU",
        "attributedUnitsOrdered14dOtherSKU",
        "attributedUnitsOrdered30dOtherSKU",
        "attributedSales1dOtherSKU",
        "attributedSales7dOtherSKU",
        "attributedSales14dOtherSKU",
        "attributedSales30dOtherSKU",
    ],
}


class Reports(AdClient):
    """
    Reports
    """

    def create_report(self, params):
        spon = params.get("spon")
        record_type = params.get("record_type")
        interface = "{spon}/{record_type}/report".format(
            spon=spon, record_type=record_type
        )

        rp_common = "{}_common".format(spon)
        metrics_list = REPORT_TYPE.get(record_type) + REPORT_TYPE.get(
            rp_common
        )
        payload = {
            "reportDate": params.get("reportDate"),
            "metrics": ",".join(metrics_list),
        }
        if ("targets") in interface:
            payload["segment"] = "query"
        return self.excute_req(
            interface, method="POST", scope=self.scope, payload=payload
        )

    def create_asins_report(self, params, profile_type=None):
        interface = "asins/report"
        metrics = REPORT_TYPE.get("asins", []).copy()

        if profile_type and profile_type != "vendor":
            metrics += REPORT_TYPE.get("asins_for_seller", []).copy()
        payload = {
            "reportDate": params.get("reportDate"),
            "metrics": ",".join(REPORT_TYPE.get("asins")),
            "campaignType": params.get("campaignType"),
        }
        if ("sp/keywords" or "targets") in interface:
            payload["segment"] = "query"
        return self.excute_req(
            interface, method="POST", scope=self.scope, payload=payload
        )

    def get_report(self, report_id):
        interface = "reports/{}".format(report_id)
        return self.excute_req(interface, method="GET", scope=self.scope)

    def download_report(self, report_id):
        interface = "reports/{}/download".format(report_id)
        report = self.excute_req(
            interface, method="DOWNLOAD", scope=self.scope
        )
        try:
            report = gzip.decompress(report.content)
            report_json = json.loads(report.decode())
            return report_json
        except Exception as e:
            raise ADAPIException(e)

    def create_snapshot(self, params):
        interface = "{spon}/{record_type}/snapshot".format(
            spon=params.get("spon"), record_type=params.get("record_type")
        )
        payload = params.get("payload")
        return self.excute_req(
            interface, method="POST", scope=self.scope, payload=payload
        )

    def get_snapshot(self, params):
        interface = "{spon}/snapshots/{snapshot_id}".format(
            spon=params.get("spon"), snapshot_id=params.get("snapshot_id")
        )
        return self.excute_req(interface, method="GET", scope=self.scope)

    def download_snapshot(self, snapshot_id):
        interface = "snapshots/{}/download".format(snapshot_id)
        report = self.excute_req(
            interface, method="DOWNLOAD", scope=self.scope
        )

        try:
            report_json = json.loads(report.content.decode())
            return report_json
        except Exception as e:
            raise ADAPIException(e)
