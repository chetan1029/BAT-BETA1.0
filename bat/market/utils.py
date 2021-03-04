from django.conf import settings

import requests
from urllib.parse import urlencode


def generate_uri(url, query_parameters):
    qp = urlencode(query_parameters)
    return url + "?" + qp


class AmazonAPI(object):

    @classmethod
    def get_oauth2_token(cls, account_credentails):
        url = settings.AMAZON_LWA_TOKEN_ENDPOINT
        form_data = {
            "grant_type": "authorization_code",
            "code": account_credentails.spapi_oauth_code,
            "client_id": settings.LWA_CLIENT_ID,
            "client_secret": settings.LWA_CLIENT_SECRET,
        }
        try:
            response = requests.post(url, data=form_data)
            response_data = {}
            if response.status_code == requests.codes.ok:
                response_data = response.json()
                return True, response_data
            else:
                response.raise_for_status()
        except requests.exceptions.HTTPError:
            return False, {"code": response.status_code, "data": response.json()}
