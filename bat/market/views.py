import base64
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views import View
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from sp_api.base import Marketplaces

from bat.company.models import Company
from bat.company.utils import get_member
from bat.market import serializers
from bat.market.amazon_sp_api.amazon_sp_api import Catalog
from bat.market.models import (
    AmazonAccountCredentails,
    AmazonAccounts,
    AmazonMarketplace,
    AmazonOrder,
    AmazonProduct,
)
from bat.market.utils import AmazonAPI, generate_uri

User = get_user_model()


class AmazonProductViewsets(viewsets.ReadOnlyModelViewSet):
    queryset = AmazonProduct.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.AmazonProductSerializer

    def filter_queryset(self, queryset):
        company_id = self.kwargs.get("company_pk", None)
        queryset = super().filter_queryset(queryset)
        return queryset.filter(
            amazonaccounts__company__id=company_id
        ).order_by("-create_date")


class AmazonOrderViewsets(viewsets.ReadOnlyModelViewSet):
    queryset = AmazonOrder.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.AmazonOrderSerializer

    def filter_queryset(self, queryset):
        company_id = self.kwargs.get("company_pk", None)
        queryset = super().filter_queryset(queryset)
        return queryset.filter(
            amazonaccounts__company__id=company_id
        ).order_by("-create_date")


class AmazonMarketplaceViewsets(viewsets.ReadOnlyModelViewSet):
    queryset = AmazonMarketplace.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.AmazonMarketplaceSerializer


class AmazonAccountsAuthorization(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, company_pk=None, market_pk=None, **kwargs):
        def _get_status_with_timestamp(member, market):
            current_timestamp = datetime.now().timestamp()
            return (
                str(member.user.username)
                + "/"
                + str(member.company.id)
                + "/"
                + str(current_timestamp)
                + "/"
                + str(market.id)
            )

        member = get_member(company_id=company_pk, user_id=request.user.id)
        market = get_object_or_404(AmazonMarketplace, pk=market_pk)

        member_with_timestamp = _get_status_with_timestamp(member, market)

        url = settings.SELLING_REGIONS.get(market.region).get("auth_url")

        state = base64.b64encode(member_with_timestamp.encode("ascii")).decode(
            "ascii"
        )
        query_parameters = {
            "state": state,
            "application_id": settings.AMAZON_APPLICATION_ID,
            "version": "beta",
        }
        OAuth_uri = generate_uri(url=url, query_parameters=query_parameters)
        return Response({"consent_uri": OAuth_uri}, status=status.HTTP_200_OK)


# https://api.thebatonline.com/test/auth-callback/amazon-marketplaces/


class AccountsReceiveAmazonCallback(View):
    def get(self, request, **kwargs):

        state = request.GET.get("state")
        mws_auth_token = request.GET.get("mws_auth_token")
        selling_partner_id = request.GET.get("selling_partner_id")
        spapi_oauth_code = request.GET.get("spapi_oauth_code")

        try:
            state = base64.b64decode(state.encode("ascii")).decode("ascii")
        except Exception as e:
            return HttpResponseRedirect(
                settings.MARKET_LIST_URI + "?error=status_cant_decode"
            )

        state_array = state.split("/")

        old_timestamp = float(state_array[2])
        old_datetime = datetime.fromtimestamp(old_timestamp)
        datetime_now = datetime.now()
        timedelta_diff = datetime_now - old_datetime
        minutes = divmod(timedelta_diff.total_seconds(), 60)[0]

        if minutes <= 5.0:
            user = get_object_or_404(User, username=state_array[0])
            company = get_object_or_404(Company, pk=state_array[1])
            marketplace = get_object_or_404(
                AmazonMarketplace, pk=state_array[3]
            )

            account_credentails, _c = AmazonAccountCredentails.objects.update_or_create(
                user=user,
                company=company,
                selling_partner_id=selling_partner_id,
                region=marketplace.region,
                defaults={
                    "mws_auth_token": mws_auth_token,
                    "spapi_oauth_code": spapi_oauth_code,
                },
            )

            _new_account, _c = AmazonAccounts.objects.get_or_create(
                marketplace=marketplace,
                user=user,
                company=company,
                defaults={"credentails": account_credentails},
            )

            # get access_token using spapi_oauth_code
            is_successfull, data = AmazonAPI.get_oauth2_token(
                account_credentails
            )

            if is_successfull:
                account_credentails.access_token = data.get("access_token")
                account_credentails.refresh_token = data.get("refresh_token")
                account_credentails.expires_at = timezone.now() + timedelta(
                    seconds=data.get("expires_in")
                )
                account_credentails.save()
                return HttpResponseRedirect(
                    settings.MARKET_LIST_URI + "?success=account_created"
                )
            else:
                return HttpResponseRedirect(
                    settings.MARKET_LIST_URI + "?error=oauth_api_call_failed"
                )
        return HttpResponseRedirect(
            settings.MARKET_LIST_URI + "?error=status_expired"
        )


class TestAmazonClientCatalog(View):
    def get(self, request, **kwargs):
        ac = AmazonAccountCredentails.objects.get(pk=14)
        print("ac :", ac)

        data = Catalog(
            marketplace=Marketplaces.US,
            refresh_token=ac.refresh_token,
            credentials={
                "refresh_token": ac.refresh_token,
                "lwa_app_id": settings.LWA_CLIENT_ID,
                "lwa_client_secret": settings.LWA_CLIENT_SECRET,
                "aws_access_key": settings.AWS_ACCESS_KEY_ID,
                "aws_secret_key": settings.AWS_SECRET_ACCESS_KEY,
                "role_arn": settings.ROLE_ARN,
            },
        ).list_items(MarketplaceId="ATVPDKIKX0DER", EAN="7350097670024")
        print("data :", data)
        return HttpResponse("data!")
