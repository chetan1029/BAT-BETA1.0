import csv
import time
import base64
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views import View
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from sp_api.base import Marketplaces
from sp_api.base.reportTypes import ReportType

from bat.company.models import Company
from bat.company.utils import get_member
from bat.market import serializers
from bat.market.amazon_sp_api.amazon_sp_api import Catalog, Reports, Orders
from bat.market.models import (
    AmazonAccountCredentails,
    AmazonAccounts,
    AmazonMarketplace,
    AmazonOrder,
    AmazonProduct,
)
from bat.market.utils import AmazonAPI, generate_uri, set_default_email_campaign_templates
from bat.market.report_parser import ReportAmazonProductCSVParser, ReportAmazonOrdersCSVParser
from bat.market.orders_data_builder import AmazonOrderProcessData

# from sp_api.api.reports.reports import Reports

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
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["name"]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        company_id = self.kwargs.get("company_pk", None)
        context["company_id"] = company_id
        context["user"] = self.request.user
        return context


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

            _new_account, amazon_accounts_is_created = AmazonAccounts.objects.get_or_create(
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

                try:
                    if amazon_accounts_is_created:
                        set_default_email_campaign_templates(
                            company=company, marketplace=marketplace)
                except Exception as e:
                    return HttpResponseRedirect(
                        settings.MARKET_LIST_URI + "?error=" + e
                    )

                return HttpResponseRedirect(
                    settings.MARKET_LIST_URI + "?success=Your " +
                    marketplace.name + "marketplace account successfully linked."
                )
            else:
                return HttpResponseRedirect(
                    settings.MARKET_LIST_URI + "?error=Your " + marketplace.name +
                    "marketplace account couldn't be linked due to: oauth_api_call_failed"
                )
        return HttpResponseRedirect(
            settings.MARKET_LIST_URI + "?error=status_expired"
        )


class TestAmazonClientCatalog(View):
    def get(self, request, **kwargs):
        ac = AmazonAccountCredentails.objects.get(pk=2)
        amazon_account = AmazonAccounts.objects.get(pk=25)
        # (not give list of products)
        # data = Catalog(
        #     marketplace=Marketplaces.US,
        #     refresh_token=ac.refresh_token,
        #     credentials={
        #         "refresh_token": ac.refresh_token,
        #         "lwa_app_id": settings.LWA_CLIENT_ID,
        #         "lwa_client_secret": settings.LWA_CLIENT_SECRET,
        #         "aws_access_key": settings.AWS_ACCESS_KEY_ID,
        #         "aws_secret_key": settings.AWS_SECRET_ACCESS_KEY,
        #         "role_arn": settings.ROLE_ARN,
        #     },
        # ).list_items(MarketplaceId="ATVPDKIKX0DER", EAN="7350097670024")

        # (1)
        # data1 = Reports(
        #     marketplace=Marketplaces["US"],
        #     refresh_token=ac.refresh_token,
        #     credentials={
        #         "refresh_token": ac.refresh_token,
        #         "lwa_app_id": settings.LWA_CLIENT_ID,
        #         "lwa_client_secret": settings.LWA_CLIENT_SECRET,
        #         "aws_access_key": settings.AWS_ACCESS_KEY_ID,
        #         "aws_secret_key": settings.AWS_SECRET_ACCESS_KEY,
        #         "role_arn": settings.ROLE_ARN,
        #     }
        #     # ).create_report(reportType=ReportType.GET_AMAZON_FULFILLED_SHIPMENTS_DATA_GENERAL,
        # ).create_report(reportType=ReportType.GET_FLAT_FILE_ALL_ORDERS_DATA_BY_ORDER_DATE_GENERAL,
        #                 dataStartTime=(datetime.utcnow() - timedelta(days=6)).isoformat(),
        #                 dataEndTime=(datetime.utcnow()).isoformat(),
        #                 marketplaceIds=[
        #                     "ATVPDKIKX0DER"
        #                 ])
        # print("data1 : ", data1)
        # reportId = int(data1.payload["reportId"])

        # (2)
        # iteration = 1
        # payload2 = {}
        # while payload2.get("processingStatus", None) != "DONE":
        #     data2 = Reports(
        #         marketplace=Marketplaces.US,
        #         refresh_token=ac.refresh_token,
        #         credentials={
        #             "refresh_token": ac.refresh_token,
        #             "lwa_app_id": settings.LWA_CLIENT_ID,
        #             "lwa_client_secret": settings.LWA_CLIENT_SECRET,
        #             "aws_access_key": settings.AWS_ACCESS_KEY_ID,
        #             "aws_secret_key": settings.AWS_SECRET_ACCESS_KEY,
        #             "role_arn": settings.ROLE_ARN,
        #         }
        #     ).get_report(reportId)
        #     payload2 = data2.payload
        #     if payload2.get("processingStatus", None) != "DONE":
        #         time.sleep(10)
        #     print(iteration, "\n")
        #     iteration = iteration + 1
        #     if(iteration > 10):
        #         break

        # print("payload2......... :", payload2)

        # (3)
        # f = open("GET_AMAZON_FULFILLED_SHIPMENTS_DATA_GENERAL.csv", "w+")
        # f = open("GET_FLAT_FILE_ALL_ORDERS_DATA_BY_ORDER_DATE_GENERAL.csv", "w+")
        # print("\n\n\n\n\n\n\n\nfile  : ", f)
        # data3 = Reports(
        #     marketplace=Marketplaces.US,
        #     refresh_token=ac.refresh_token,
        #     credentials={
        #         "refresh_token": ac.refresh_token,
        #         "lwa_app_id": settings.LWA_CLIENT_ID,
        #         "lwa_client_secret": settings.LWA_CLIENT_SECRET,
        #         "aws_access_key": settings.AWS_ACCESS_KEY_ID,
        #         "aws_secret_key": settings.AWS_SECRET_ACCESS_KEY,
        #         "role_arn": settings.ROLE_ARN,
        #     },
        # ).get_report_document(payload2["reportDocumentId"], decrypt=True, file=f)

        # (4)
        orders_items_report_csv = open("GET_AMAZON_FULFILLED_SHIPMENTS_DATA_GENERAL.csv", "r")
        orders_report_csv = open("GET_FLAT_FILE_ALL_ORDERS_DATA_BY_ORDER_DATE_GENERAL.csv", "r")
        data, order_columns, item_columns = ReportAmazonOrdersCSVParser.parse(
            orders_report_csv, orders_items_report_csv)
        print("\n\n\n\n\n\n\n\n\n\n\n\n")
        print("data : ", data)
        is_created = AmazonOrder.objects.create_bulk(
            data, amazon_account, order_columns, item_columns)
        print("\n\n\n\n\n\n\n\n\n\n\n\n")
        print(is_created)

        # (4)
        # report_csv = open("test_report.csv", "r")
        # data, columns = ReportAmazonProductCSVParser.parse(report_csv)
        # is_created = AmazonProduct.objects.import_bulk(data, amazon_account, columns)

        # ###### Orders ######
        # Step 1
        # data = Orders(
        #     marketplace=Marketplaces.US,
        #     refresh_token=ac.refresh_token,
        #     credentials={
        #         "refresh_token": ac.refresh_token,
        #         "lwa_app_id": settings.LWA_CLIENT_ID,
        #         "lwa_client_secret": settings.LWA_CLIENT_SECRET,
        #         "aws_access_key": settings.AWS_ACCESS_KEY_ID,
        #         "aws_secret_key": settings.AWS_SECRET_ACCESS_KEY,
        #         "role_arn": settings.ROLE_ARN,
        #     },
        # ).get_orders(CreatedAfter=(datetime.utcnow() - timedelta(days=6)).isoformat())
        # print(data)
        # c_data = AmazonOrderProcessData.builder(data.payload["Orders"], amazon_account)
        # print("\n\n\n\n\n\n\n\n\n\n\n")
        # print(c_data)

        # Data point mapping
        # AmazonOrderId = order_id
        # SellerOrderId = order_seller_id
        # PurchaseDate = purchase_date
        # PurchaseDate = payment_date
        # EarliestShipDate = shipment_date
        # LastUpdateDate = reporting_date
        # IsReplacementOrder = replacement
        # OrderStatus = status
        # SalesChannel = sales_channel
        # NumberOfItemsShipped+NumberOfItemsUnshipped = quantity
        # OrderTotal = amount

        # Step 2
        # next_token = data.next_token
        # while next_token:
        #     data2 = Orders(
        #         marketplace=Marketplaces.US,
        #         refresh_token=ac.refresh_token,
        #         credentials={
        #             "refresh_token": ac.refresh_token,
        #             "lwa_app_id": settings.LWA_CLIENT_ID,
        #             "lwa_client_secret": settings.LWA_CLIENT_SECRET,
        #             "aws_access_key": settings.AWS_ACCESS_KEY_ID,
        #             "aws_secret_key": settings.AWS_SECRET_ACCESS_KEY,
        #             "role_arn": settings.ROLE_ARN,
        #         },
        #     ).get_orders(NextToken=next_token)

        #     next_token = data2.next_token

        #     c_data = c_data + \
        #         AmazonOrderProcessData.builder(data2.payload["Orders"], amazon_account)

        #     print("\n\n\n\n\n\n\n\n\n\n\n")
        #     print("next_token : ", next_token)

        #     print("\n\n\n\n\n\n\n\n\n\n\n")

        # print(c_data)

        # is_created = AmazonOrder.objects.create_bulk(c_data)

        # Step 3
        # data = Orders(
        #     marketplace=Marketplaces.US,
        #     refresh_token=ac.refresh_token,
        #     credentials={
        #         "refresh_token": ac.refresh_token,
        #         "lwa_app_id": settings.LWA_CLIENT_ID,
        #         "lwa_client_secret": settings.LWA_CLIENT_SECRET,
        #         "aws_access_key": settings.AWS_ACCESS_KEY_ID,
        #         "aws_secret_key": settings.AWS_SECRET_ACCESS_KEY,
        #         "role_arn": settings.ROLE_ARN,
        #     },
        # ).get_order_items("111-9508492-9812214")

        # Data point mapping
        # OrderItemId = item_id
        # ASIN and SellerSKU check on amazonproduct = amazonproduct
        # NumberOfItems = quantity
        # ASIN = asin
        # ItemPrice = item_price
        # ItemTax = item_tax
        # PromotionDiscount = item_promotional_discount

        # data = Orders(
        #     marketplace=Marketplaces.US,
        #     refresh_token=ac.refresh_token,
        #     credentials={
        #         "refresh_token": ac.refresh_token,
        #         "lwa_app_id": settings.LWA_CLIENT_ID,
        #         "lwa_client_secret": settings.LWA_CLIENT_SECRET,
        #         "aws_access_key": settings.AWS_ACCESS_KEY_ID,
        #         "aws_secret_key": settings.AWS_SECRET_ACCESS_KEY,
        #         "role_arn": settings.ROLE_ARN,
        #     },
        # ).get_order_buyer_info("111-9508492-9812214")

        # BuyerEmail = buyer_email in the Amazonorder table

        return HttpResponse()
