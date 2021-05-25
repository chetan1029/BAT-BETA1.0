# coding: utf-8
from .ad_client import AdClient


class ProductAds(AdClient):
    """
    Product Ads
    """

    def get_productad(self, adid):
        interface = 'sp/productAds/{}'.format(adid)
        return self.excute_req(interface, scope=self.scope)

    def get_productad_ex(self, adid):
        interface = 'sp/productAds/extended/{}'.format(adid)
        return self.excute_req(interface, scope=self.scope)

    def create_productad(self, params):
        interface = 'sp/productAds'
        payload = params.get('payload')
        return self.excute_req(interface, method='POST', scope=self.scope, payload=payload)

    def update_productad(self, params):
        interface = 'sp/productAds'
        payload = params.get('payload')
        return self.excute_req(interface, method='PUT', scope=self.scope, payload=payload)

    def delete_productad(self, adid):
        interface = 'sp/productAds/{}'.format(adid)
        return self.excute_req(interface, method='DELETE', scope=self.scope)

    def list_productads(self, params):
        interface = 'sp/productAds'
        payload = {
            'startIndex': params.get('startIndex'),
            'count': params.get('count'),
            'sku': params.get('sku'),
            'asin': params.get('asin'),
            'stateFilter': params.get('stateFilter'),
            'adGroupIdFilter': params.get('adGroupIdFilter'),
            'campaignIdFilter': params.get('campaignIdFilter')
        }
        return self.excute_req(interface, scope=self.scope, payload=payload)

    def list_productads_ex(self, params):
        interface = 'sp/productAds/extended'
        payload = {
            'startIndex': params.get('startIndex'),
            'count': params.get('count'),
            'adGroupId': params.get('adGroupId'),
            'sku': params.get('sku'),
            'asin': params.get('asin'),
            'stateFilter': params.get('stateFilter'),
            'adGroupIdFilter': params.get('adGroupIdFilter'),
            'campaignIdFilter': params.get('campaignIdFilter')
        }
        return self.excute_req(interface, scope=self.scope, payload=payload)