import json
from sp_api.base import client
from sp_api.base.exceptions import get_exception_for_code
from sp_api.base.ApiResponse import ApiResponse


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

    @staticmethod
    def _check_response(res) -> ApiResponse:
        # error = json.loads(res.text, strict=False).get('errors', None)
        # if error:
        #     exception = get_exception_for_code(res.status_code)
        #     raise exception(error)
        json_res = json.loads(res.text, strict=False)
        return ApiResponse(**json_res, headers=res.headers)
