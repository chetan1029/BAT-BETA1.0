from sp_api.base import client

from bat.market.amazon_sp_api.auth_access_token_client import AuthAccessTokenClient


class APIClient(client.Client):
    def __init__(
        self,
        marketplace,
        refresh_token=None,
        account='default',
        credentials=None
    ):
        super().__init__(marketplace, refresh_token=refresh_token, account=account, credentials=credentials)
        self._auth = AuthAccessTokenClient(
            refresh_token=refresh_token, account=account, credentials=credentials)
