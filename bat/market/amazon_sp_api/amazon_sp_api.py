import urllib.parse
import zlib
from collections import abc
from datetime import datetime

import requests
from sp_api.base import (
    ApiResponse,
    Marketplaces,
    SellingApiException,
    fill_query_params,
    sp_endpoint,
)
from sp_api.base.helpers import decrypt_aes

from bat.market.amazon_sp_api.base_client import APIClient


class Catalog(APIClient):
    @sp_endpoint("/catalog/v0/items/{}")
    def get_item(self, asin: str, **kwargs) -> ApiResponse:
        return self._request(
            fill_query_params(kwargs.pop("path"), asin), params=kwargs
        )

    @sp_endpoint("/catalog/v0/items")
    def list_items(self, **kwargs) -> ApiResponse:
        if "Query" in kwargs:
            kwargs.update(
                {"Query": urllib.parse.quote_plus(kwargs.pop("Query"))}
            )
        return self._request(kwargs.pop("path"), params=kwargs)


class Orders(APIClient):
    @sp_endpoint("/orders/v0/orders")
    def get_orders(self, **kwargs) -> ApiResponse:
        return self._request(kwargs.pop("path"), params={**kwargs})

    @sp_endpoint("/orders/v0/orders/{}")
    def get_order(self, order_id: str, **kwargs) -> ApiResponse:
        return self._request(
            fill_query_params(kwargs.pop("path"), order_id),
            params={**kwargs},
            add_marketplace=False,
        )

    @sp_endpoint("/orders/v0/orders/{}/orderItems")
    def get_order_items(self, order_id: str, **kwargs) -> ApiResponse:
        return self._request(
            fill_query_params(kwargs.pop("path"), order_id), params={**kwargs}
        )

    @sp_endpoint("/orders/v0/orders/{}/address")
    def get_order_address(self, order_id, **kwargs) -> ApiResponse:
        return self._request(
            fill_query_params(kwargs.pop("path"), order_id), params={**kwargs}
        )

    @sp_endpoint("/orders/v0/orders/{}/buyerInfo")
    def get_order_buyer_info(self, order_id: str, **kwargs) -> ApiResponse:
        return self._request(
            fill_query_params(kwargs.pop("path"), order_id), params={**kwargs}
        )

    @sp_endpoint("/orders/v0/orders/{}/orderItems/buyerInfo")
    def get_order_items_buyer_info(
        self, order_id: str, **kwargs
    ) -> ApiResponse:
        return self._request(
            fill_query_params(kwargs.pop("path"), order_id), params=kwargs
        )


class Reports(APIClient):
    @sp_endpoint("/reports/2020-09-04/reports", method="POST")
    def create_report(self, **kwargs) -> ApiResponse:
        """
        See report types at
        :link: https://github.com/amzn/selling-partner-api-docs/blob/main/references/reports-api/reportType_string_array_values.md
        """
        return self._request(kwargs.pop("path"), data=kwargs)

    @sp_endpoint("/reports/2020-09-04/reports/{}")
    def get_report(self, report_id, **kwargs) -> ApiResponse:
        """
        Returns report details (including the reportDocumentId, if available) for the report that you specify.
        """
        return self._request(
            fill_query_params(kwargs.pop("path"), report_id),
            add_marketplace=False,
        )

    @sp_endpoint("/reports/2020-09-04/documents/{}")
    def get_report_document(
        self, document_id, decrypt: bool = False, file=None, **kwargs
    ) -> ApiResponse:
        """
        Returns the information required for retrieving a report document's contents. This includes a presigned URL for the report document as well as the information required to decrypt the document's contents.
        If decrypt = True the report will automatically be loaded and decrypted/unpacked
        If file is set to a file (or file like object), the report's contents are written to the file
        """
        res = self._request(
            fill_query_params(kwargs.pop("path"), document_id),
            add_marketplace=False,
        )
        if decrypt:
            document = self.decrypt_report_document(
                res.payload.get("url"),
                res.payload.get("encryptionDetails").get(
                    "initializationVector"
                ),
                res.payload.get("encryptionDetails").get("key"),
                res.payload.get("encryptionDetails").get("standard"),
                res.payload,
            )
            res.payload.update({"document": document})
            if file:
                if isinstance(file, str):
                    with open(file, "w") as text_file:
                        text_file.write(document)
                else:
                    file.write(document)

        return res

    @sp_endpoint("/reports/2020-09-04/schedules", method="POST")
    def create_report_schedule(self, **kwargs) -> ApiResponse:
        """
        Creates a report schedule. If a report schedule with the same report type and marketplace IDs already exists, it will be cancelled and replaced with this one.
        """
        return self._request(kwargs.pop("path"), data=kwargs)

    @sp_endpoint("/reports/2020-09-04/schedules/{}", method="DELETE")
    def delete_report_schedule(self, schedule_id, **kwargs) -> ApiResponse:
        """
        Cancels the report schedule that you specify.
        """
        return self._request(
            fill_query_params(kwargs.pop("path"), schedule_id), params=kwargs
        )

    @sp_endpoint("/reports/2020-09-04/schedules/{}")
    def get_report_schedule(self, schedule_id, **kwargs) -> ApiResponse:
        """
        Cancels the report schedule that you specify.
        """
        return self._request(
            fill_query_params(kwargs.pop("path"), schedule_id), params=kwargs
        )

    @sp_endpoint("/reports/2020-09-04/reports")
    def get_reports(self, **kwargs) -> ApiResponse:
        """
        Returns report details for the reports that match the filters that you specify.
        """
        if kwargs.get("reportTypes", None) and isinstance(
            kwargs.get("reportTypes"), abc.Iterable
        ):
            kwargs.update({"reportTypes": ",".join(kwargs.get("reportTypes"))})
        if kwargs.get("processingStatuses", None) and isinstance(
            kwargs.get("processingStatuses"), abc.Iterable
        ):
            kwargs.update(
                {
                    "processingStatuses": ",".join(
                        kwargs.get("processingStatuses")
                    )
                }
            )
        if kwargs.get("marketplaceIds", None) and isinstance(
            kwargs.get("marketplaceIds"), abc.Iterable
        ):
            marketplaces = kwargs.get("marketplaceIds")
            if not isinstance(marketplaces, abc.Iterable):
                marketplaces = [marketplaces]
            kwargs.update(
                {
                    "marketplaceIds": ",".join(
                        [
                            m.marketplace_id
                            if isinstance(m, Marketplaces)
                            else m
                            for m in marketplaces
                        ]
                    )
                }
            )
        for k in ["createdSince", "createdUntil"]:
            if kwargs.get(k, None) and isinstance(kwargs.get(k), datetime):
                kwargs.update({k: kwargs.get(k).isoformat()})

        return self._request(
            kwargs.pop("path"), params=kwargs, add_marketplace=False
        )

    @staticmethod
    def decrypt_report_document(
        url, initialization_vector, key, encryption_standard, payload
    ):
        """
        Decrypts and unpacks a report document, currently AES encryption is implemented
        """
        if encryption_standard == "AES":
            decrypted = decrypt_aes(
                requests.get(url).content, key, initialization_vector
            )
            if "compressionAlgorithm" in payload:
                return zlib.decompress(bytearray(decrypted), 15 + 32).decode(
                    "iso-8859-1"
                )
            return decrypted.decode("iso-8859-1")
        raise SellingApiException(
            [
                {
                    "message": "Only AES decryption is implemented. Contribute: https://github.com/saleweaver/python-sp-api"
                }
            ]
        )
