# coding: utf-8
from . import ad_client


class Campaigns(ad_client.AdClient):
    """
    Campaigns
    """

    def get_campaign(self, campaign_id, params):
        interface = '{spon}/campaigns/{campaign_id}'.format(
            spon=params.get('spon'),
            campaign_id=campaign_id
        )
        return self.excute_req(interface, scope=self.scope)

    def get_campaign_ex(self, campaign_id, params):
        interface = '{spon}/campaigns/extended/{campaign_id}'.format(
            spon=params.get('spon'),
            campaign_id=campaign_id
        )
        return self.excute_req(interface, scope=self.scope)

    def create_campaigns(self, params):
        interface = 'sp/campaigns'
        payload = params.get('payload')
        return self.excute_req(interface, method='POST', scope=self.scope, payload=payload)

    def update_campaigns(self, params):
        interface = '{}/campaigns'.format(params.get('spon'))
        payload = params.get('payload')
        return self.excute_req(interface, method='PUT', scope=self.scope, payload=payload)

    def delete_campaign(self, campaign_id, params):
        interface = '{spon}/campaigns/{campaign_id}'.format(
            spon=params.get('spon'),
            campaign_id=campaign_id
        )
        return self.excute_req(interface, method='DELETE', scope=self.scope)

    def list_campaigns(self, params):
        interface = '{}/campaigns'.format(params.get('spon'))
        payload = {
            'startIndex': params.get('startIndex'),
            'count': params.get('count'),
            'stateFilter': params.get('stateFilter'),
            'name': params.get('name'),
            'portfolioIdFilter': params.get('portfolioIdFilter'),
            'campaignIdFilter': params.get('campaignIdFilter')
        }
        return self.excute_req(interface, scope=self.scope, payload=payload)

    def list_campaigns_ex(self, params):
        interface = '{}/campaigns/extended'.format(params.get('spon'))
        payload = {
            'startIndex': params.get('startIndex'),
            'count': params.get('count'),
            'stateFilter': params.get('stateFilter'),
            'name': params.get('name'),
            'campaignIdFilter': params.get('campaignIdFilter')
        }
        return self.excute_req(interface, scope=self.scope, payload=payload)
