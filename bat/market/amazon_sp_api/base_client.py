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
        # print("res.text : ", res.text)
        # error = json.loads(res.text, strict=False).get('errors', None)
        # print("error : ", error, "\n\n status_code", res.status_code)
        # if error:
        #     exception = get_exception_for_code(res.status_code)
        #     raise exception(error)
        return ApiResponse(**json.loads(res.text, strict=False), headers=res.headers)
