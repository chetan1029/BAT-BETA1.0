# coding:utf-8
import datetime
import json

import requests

from django.conf import settings

from .exception import ADAPIException

API_VERSION = "v2"


class AdClient(object):
    """
    Amazon AD API client
    """

    def __init__(
        self,
        access_token,
        refresh_token,
        scope=None,
        region=settings.AMAZON_PPC_REGION,
    ):
        self.client_id = settings.AMAZON_PPC_CLIENT_ID
        self.client_secret = settings.AMAZON_PPC_CLIENT_SECRET
        self._access_token = access_token
        self.refresh_token = refresh_token
        self.scope = scope
        self.oauth_url = settings.AMAZON_PPC_TOKEN_ENDPOINT
        self.region = region

    @property
    def access_token(self):
        return self._access_token

    @access_token.setter
    def access_token(self, value):
        self._access_token = value

    def do_refresh_token(self):
        headers = {"Content-Type": "application/json"}
        data = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
        }
        resp = requests.post(
            self.oauth_url, headers=headers, data=json.dumps(data)
        )
        self._access_token = dict(resp.json()).get("access_token")

    def list_profiles(self):
        interface = "profiles"
        return self.excute_req(interface)

    def get_profile(self, profile_id):
        interface = "profiles/{}".format(profile_id)
        return self.excute_req(interface)

    def create_sandbox_profile(self):
        interface = "profiles"
        payload = {"countryCode": "US"}
        return self.excute_req(
            interface,
            method="PUT",
            scope=None,
            payload=payload,
            region="advertising-api-test.amazon.com",
        )

    def excute_req(
        self, interface, method="GET", scope=None, payload=None, region=None
    ):
        headers = {
            "Content-Type": "application/json",
            "Amazon-Advertising-API-ClientId": self.client_id,
            "Authorization": "Bearer {}".format(self._access_token),
        }
        host = region if region else self.region
        url = "https://{host}/{version}/{interface}".format(
            host=host, version=API_VERSION, interface=interface
        )
        print(
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            + " "
            + method
            + " "
            + url
        )
        if scope:
            headers["Amazon-Advertising-API-Scope"] = str(scope)
        if method == "GET":
            try:
                resp = (
                    requests.get(url, headers=headers, params=payload)
                    if payload
                    else requests.get(url, headers=headers)
                )
                resp.raise_for_status()
                return resp.json()
            except requests.exceptions.HTTPError as errh:
                raise ADAPIException(
                    errh.response.json(), status_code=errh.response.status_code
                )
            except requests.exceptions.ConnectionError as errc:
                raise ADAPIException(errc)
            except requests.exceptions.Timeout as errt:
                raise ADAPIException(errt)
            except requests.exceptions.RequestException as err:
                raise ADAPIException(err)
        elif method == "POST":
            try:
                resp = (
                    requests.post(
                        url, headers=headers, data=json.dumps(payload)
                    )
                    if payload
                    else requests.post(url, headers=headers)
                )
                resp.raise_for_status()
                return resp.json()
            except requests.exceptions.HTTPError as errh:
                raise ADAPIException(
                    errh.response.json(), status_code=errh.response.status_code
                )
            except requests.exceptions.ConnectionError as errc:
                raise ADAPIException(errc)
            except requests.exceptions.Timeout as errt:
                raise ADAPIException(errt)
            except requests.exceptions.RequestException as err:
                raise ADAPIException(err)
        elif method == "PUT":
            try:
                resp = (
                    requests.put(
                        url, headers=headers, data=json.dumps(payload)
                    )
                    if payload
                    else requests.put(url, headers=headers)
                )
                resp.raise_for_status()
                return resp.json()
            except requests.exceptions.HTTPError as errh:
                raise ADAPIException(
                    errh.response.json(), status_code=errh.response.status_code
                )
            except requests.exceptions.ConnectionError as errc:
                raise ADAPIException(errc)
            except requests.exceptions.Timeout as errt:
                raise ADAPIException(errt)
            except requests.exceptions.RequestException as err:
                raise ADAPIException(err)
        elif method == "DELETE":
            try:
                resp = requests.delete(url, headers=headers)
                resp.raise_for_status()
                return True
            except requests.exceptions.HTTPError as errh:
                raise ADAPIException(
                    errh.response.json(), status_code=errh.response.status_code
                )
            except requests.exceptions.ConnectionError as errc:
                raise ADAPIException(errc)
            except requests.exceptions.Timeout as errt:
                raise ADAPIException(errt)
            except requests.exceptions.RequestException as err:
                raise ADAPIException(err)
        elif method == "DOWNLOAD":
            headers.pop("Content-Type")
            try:
                resp = (
                    requests.get(
                        url, headers=headers, params=payload, stream=True
                    )
                    if payload
                    else requests.get(url, headers=headers)
                )
                resp.raise_for_status()
                return resp
            except requests.exceptions.HTTPError as errh:
                raise ADAPIException(
                    errh.response.json(), status_code=errh.response.status_code
                )
            except requests.exceptions.ConnectionError as errc:
                raise ADAPIException(errc)
            except requests.exceptions.Timeout as errt:
                raise ADAPIException(errt)
            except requests.exceptions.RequestException as err:
                raise ADAPIException(err)

            # with requests.get(url, headers=headers, stream=True) as r:
            #     with open(local_filepath, 'wb') as f:
            #         shutil.copyfileobj(r.raw, f)
            # return local_filepath
