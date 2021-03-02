import random
import string
import base64

from datetime import datetime
from django.conf import settings
from django.contrib.auth import get_user_model


from rest_framework.views import APIView
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from bat.market import serializers
from bat.market.models import AmazonMarketplace, AmazonAccounts
from bat.market.utils import CryptoCipher, generate_uri
from bat.company.utils import get_member
from bat.company.models import Company

User = get_user_model()


class AmazonMarketplaceViewsets(viewsets.ReadOnlyModelViewSet):
    queryset = AmazonMarketplace.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.AmazonMarketplaceSerializer


class AmazonAccountsAuthorization(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, company_pk=None, market_pk=None, **kwargs):
        def _get_member_str_with_timestamp(member):
            current_timestamp = datetime.now().timestamp()
            return str(member.user.username) + "/" + str(member.company.id) + "/" + str(current_timestamp) + "/"

        member = get_member(company_id=company_pk, user_id=request.user.id)

        member_with_timestamp = _get_member_str_with_timestamp(member)
        print("member_with_timestamp : ", member_with_timestamp)

        # while len(bytes(member_with_timestamp, encoding='utf-8')) % 16 != 0:
        #     member_with_timestamp = member_with_timestamp + random.choice(string.ascii_letters)

        url = settings.AMAZON_SELLER_CENTRAL_AUTHORIZE_URL
        state = base64.b64encode(member_with_timestamp.encode("ascii")).decode("ascii")
        query_parameters = {
            "state": state,
            "application_id": "tempid",
            "version": "beta"
        }
        OAuth_uri = generate_uri(url=url, query_parameters=query_parameters)
        return Response({"consent_uri": OAuth_uri}, status=status.HTTP_200_OK)


class AccountsReceiveAmazonCallback(APIView):

    def post(self, request, **kwargs):
        state = request.GET.get('state')
        mws_auth_token = request.GET.get('mws_auth_token')
        selling_partner_id = request.GET.get('selling_partner_id')
        spapi_oauth_code = request.GET.get('spapi_oauth_code')

        state = base64.b64decode(state.encode("ascii")).decode("ascii")
        dt_array = state.split("/")

        old_timestamp = float(dt_array[2])
        old_datetime = datetime.fromtimestamp(old_timestamp)
        datetime_now = datetime.now()

        timedelta = datetime_now - old_datetime
        minutes = divmod(timedelta.total_seconds(), 60)[0]
        if minutes <= 5.0:
            user = User.objects.get(username=dt_array[0])
            company = Company.objects.get(pk=dt_array[1])
            marketplace = AmazonMarketplace.objects.get(pk=1)
            AmazonAccounts.objects.create(marketplace=marketplace,
                                          user=user,
                                          company=company,
                                          selling_partner_id=selling_partner_id,
                                          mws_auth_token=mws_auth_token,
                                          spapi_oauth_code=spapi_oauth_code
                                          )
        return Response()
