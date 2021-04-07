# import pytz
import logging
from datetime import datetime, timedelta

from django.utils import timezone

from sp_api.auth.access_token_client import AccessTokenClient
from sp_api.auth.access_token_response import AccessTokenResponse
from cachetools import TTLCache


from bat.market.models import AmazonAccountCredentails

cache = TTLCache(maxsize=10, ttl=3600)
grantless_cache = TTLCache(maxsize=10, ttl=3600)
logger = logging.getLogger(__name__)
# utc = pytz.UTC


class AuthAccessTokenClient(AccessTokenClient):
    def get_auth(self) -> AccessTokenResponse:
        """
        Get's the access token
        :return:AccessTokenResponse
        """
#

        global cache

        cache_key = self._get_cache_key()
        try:
            access_token = cache[cache_key]
            logger.debug('from cache')
        except KeyError:
            account_credentails = AmazonAccountCredentails.objects.get(
                refresh_token=self.cred.refresh_token)

            request_url = self.scheme + self.host + self.path
            access_token = self._request(request_url, self.data, self.headers)

            #

            account_credentails.access_token = access_token.get("access_token")
            account_credentails.refresh_token = access_token.get("refresh_token")
            account_credentails.expires_at = timezone.now() + timedelta(seconds=access_token.get("expires_in"))
            account_credentails.save()
            #

            logger.debug('token refreshed')
            cache = TTLCache(maxsize=10, ttl=3600)
            cache[cache_key] = access_token

#
        # access_token = {}
        # account_credentails = AmazonAccountCredentails.objects.get(
        #     refresh_token=self.cred.refresh_token)
        # access_token["access_token"] = account_credentails.access_token
        # access_token["refresh_token"] = account_credentails.refresh_token
        # access_token["expires_in"] = 3600
        # access_token["token_type"] = "bearer"
        # logger.debug('access_token from db')
        # expires_time = account_credentails.expires_at.replace(tzinfo=utc)
        # if expires_time < datetime.now(tz=utc):
        #     request_url = self.scheme + self.host + self.path
        #     access_token = self._request(request_url, self.data, self.headers)
        #     account_credentails.access_token = access_token.get("access_token")
        #     account_credentails.refresh_token = access_token.get("refresh_token")
        #     account_credentails.expires_at = datetime.now() + timedelta(seconds=access_token.get("expires_in"))
        #     account_credentails.save()
        #     logger.debug('token refreshed')
        return AccessTokenResponse(**access_token)
