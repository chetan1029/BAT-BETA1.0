from django.conf import settings

import requests

from Crypto.Cipher import AES, DES


def generate_uri(url, query_parameters):
    uri = url + "?"
    for key, value in query_parameters.items():
        uri = uri + key + "=" + value + "&"
    print(uri[:-1])
    return uri[:-1]


class CryptoCipher(object):

    @classmethod
    def encrypt(cls, text):
        text = str(text)
        AES_obj = AES.new('This is a key123', AES.MODE_CBC, 'This is an IV456')
        return AES_obj.encrypt(text)

    @classmethod
    def decrypt(cls, text):
        AES_obj = AES.new('This is a key123', AES.MODE_CBC, 'This is an IV456')
        plain_text = AES_obj.decrypt(text).decode("utf-8")
        return plain_text


class AmazonAPI(object):

    @classmethod
    def get_oauth2_token(cls, amazon_account):
        url = settings.AMAZON_LWA_TOKEN_ENDPOINT
        form_data = {
            "grant_type": "authorization_code",
            "code": amazon_account.spapi_oauth_code,
            "redirect_uri": "url",
            "client_id": "client_id",
            "client_secret": "client_secret"
        }
        try:
            response = requests.post(url, data=form_data)
            response_data = {}
            if response.status_code == requests.codes.ok:
                response_data = response.text
                return True, response_data
            else:
                response.raise_for_status()
        except requests.exceptions.HTTPError:
            print("error_response :", response.status_code, response.text)
            return False, {"code": response.status_code, "data": response.text}
