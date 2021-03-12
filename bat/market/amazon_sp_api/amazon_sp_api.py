import urllib.parse

from sp_api.base import ApiResponse, Marketplaces, fill_query_params, sp_endpoint

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
