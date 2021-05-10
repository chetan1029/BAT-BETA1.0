import base64
import csv
import os
import tempfile
import time
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.views import View
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from sp_api.base import Marketplaces
from sp_api.base.reportTypes import ReportType

from bat.autoemail.models import (
    EmailCampaign,
    EmailQueue,
    EmailTemplate,
    SesEmailTemplateMarketPlace,
)
from bat.autoemail.utils import update_ses_email_verification
from bat.company.models import Company
from bat.company.utils import get_member
from bat.mailsender.boto_ses import (
    is_ses_email_verified,
    verify_ses_email,
    verify_ses_email_custom_template,
)
from bat.market import serializers
from bat.market.amazon_sp_api.amazon_sp_api import (
    Catalog,
    Messaging,
    Orders,
    Reports,
    Solicitations,
)
from bat.market.constants import MARKETPLACE_CODES
from bat.market.models import (
    AmazonAccountCredentails,
    AmazonAccounts,
    AmazonCompany,
    AmazonMarketplace,
    AmazonOrder,
    AmazonProduct,
)
from bat.market.orders_data_builder import AmazonOrderProcessData
from bat.market.report_parser import (
    ReportAmazonOrdersCSVParser,
    ReportAmazonProductCSVParser,
)
from bat.market.tasks import amazon_account_products_orders_sync
from bat.market.utils import (
    AmazonAPI,
    generate_uri,
    get_amazon_report,
    get_messaging,
    get_order_messaging_actions,
    get_solicitation,
    send_amazon_review_request,
    set_default_amazon_company,
    set_default_email_campaign_templates,
)
from bat.subscription.constants import QUOTA_CODE_MARKETPLACES
from bat.subscription.utils import get_feature_by_quota_code

# from sp_api.api.reports.reports import Reports

User = get_user_model()


class AmazonProductViewsets(viewsets.ReadOnlyModelViewSet):
    queryset = AmazonProduct.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.AmazonProductSerializer

    def filter_queryset(self, queryset):
        company_id = self.kwargs.get("company_pk", None)
        _member = get_member(
            company_id=company_id, user_id=self.request.user.id
        )
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
        _member = get_member(
            company_id=company_id, user_id=self.request.user.id
        )
        queryset = super().filter_queryset(queryset)
        return queryset.filter(
            amazonaccounts__company__id=company_id
        ).order_by("-create_date")


class AmazonMarketplaceViewsets(
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = AmazonMarketplace.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.AmazonMarketplaceSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["name"]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        company_id = self.kwargs.get("company_pk", None)
        _member = get_member(
            company_id=company_id, user_id=self.request.user.id
        )
        context["company_id"] = company_id
        context["user"] = self.request.user

        return context

    def retrieve(self, request, company_pk=None, pk=None):
        market = get_object_or_404(AmazonMarketplace, pk=pk)
        try:
            accounts = AmazonAccounts.objects.get(
                marketplace=market,
                user_id=request.user.id,
                company_id=company_pk,
            )
            update_ses_email_verification(accounts.credentails)
        except ObjectDoesNotExist:
            return Response(
                {"detail": _("Markplace account record not found.")},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def partial_update(self, request, company_pk=None, pk=None, **kwargs):
        email = request.data["email"]
        market = get_object_or_404(AmazonMarketplace, pk=pk)
        try:
            accounts = AmazonAccounts.objects.get(
                marketplace=market,
                user_id=request.user.id,
                company_id=company_pk,
            )
            accounts.credentails.email = email

            # check if added email is already verified in SES by this user
            is_email_verified = AmazonAccounts.objects.filter(
                user_id=request.user.id,
                company_id=company_pk,
                credentails__email=email,
                credentails__email_verified=True,
            )
            if is_email_verified.exists():
                accounts.credentails.email_verified = True

            accounts.credentails.save()

            if not accounts.credentails.email_verified:
                # Send SES custom verification template
                ses_template = SesEmailTemplateMarketPlace.objects.filter(
                    amazonmarketplace=market
                ).first()
                ses_template_name = ses_template.sesemailtemplate.slug
                verify_ses_email_custom_template(email, ses_template_name)

        except ObjectDoesNotExist:
            return Response(
                {"detail": _("Markplace account record not found.")},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        return Response(
            {"detail": _("Account Marketplace updated.")},
            status=status.HTTP_200_OK,
        )


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

            if not AmazonAccounts.objects.filter(
                marketplace=marketplace,
                credentails__selling_partner_id=selling_partner_id,
            ).exists():

                # Change quota for user account for Marketplace according to his subsbribed plan.
                feature = get_feature_by_quota_code(
                    company, codename=QUOTA_CODE_MARKETPLACES
                )

                if feature.consumption > 0:

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

                    new_account, amazon_accounts_is_created = AmazonAccounts.objects.get_or_create(
                        marketplace=marketplace,
                        user=user,
                        company=company,
                        defaults={"credentails": account_credentails},
                    )

                    if not amazon_accounts_is_created:
                        new_account.is_active = True
                        new_account.save()

                    # get access_token using spapi_oauth_code
                    is_successfull, data = AmazonAPI.get_oauth2_token(
                        account_credentails
                    )

                    if is_successfull:
                        account_credentails.access_token = data.get(
                            "access_token"
                        )
                        account_credentails.refresh_token = data.get(
                            "refresh_token"
                        )
                        account_credentails.expires_at = timezone.now() + timedelta(
                            seconds=data.get("expires_in")
                        )
                        account_credentails.save()

                        try:
                            if amazon_accounts_is_created:
                                set_default_email_campaign_templates(
                                    company=company, marketplace=marketplace
                                )
                                set_default_amazon_company(
                                    company=company, amazonaccounts=new_account
                                )
                        except Exception as e:
                            return HttpResponseRedirect(
                                settings.MARKET_LIST_URI
                                + "auto-emails/"
                                + str(company.id)
                                + "/campaigns?error="
                                + e
                            )
                        # call task to collect data from amazon account
                        amazon_account_products_orders_sync.delay(
                            new_account.id, last_no_of_days=8
                        )

                        # Change the consumption for the markplaces in the company plan.
                        feature.consumption = feature.consumption - 1
                        feature.save()

                        return HttpResponseRedirect(
                            settings.MARKET_LIST_URI
                            + "auto-emails/"
                            + str(company.id)
                            + "/campaigns/"
                            + str(marketplace.id)
                            + "/?success=Your "
                            + marketplace.name
                            + " marketplace account successfully linked. Give us 10-15 mins to sync your orders and queue the emails."
                        )
                else:
                    return HttpResponseRedirect(
                        settings.MARKET_LIST_URI
                        + "auto-emails/"
                        + str(company.id)
                        + "/campaigns?error=Your Marketplace Quota limit is already consumed."
                    )
            else:
                return HttpResponseRedirect(
                    settings.MARKET_LIST_URI
                    + "auto-emails/"
                    + str(company.id)
                    + "/campaigns?error=This Marketplace is already connected. You can't connect same Amazon Account with mulitple Logins."
                )
        else:
            return HttpResponseRedirect(
                settings.MARKET_LIST_URI
                + "auto-emails/"
                + str(company.id)
                + "/campaigns?error=Your "
                + marketplace.name
                + " marketplace account couldn't be linked due to: oauth_api_call_failed"
            )
        return HttpResponseRedirect(
            settings.MARKET_LIST_URI
            + "auto-emails/"
            + str(company.id)
            + "/campaigns?error=status has been expired"
        )


class AmazonAccountsDisconnect(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, company_pk=None, market_pk=None, **kwargs):
        company = get_object_or_404(Company, id=company_pk)
        _member = get_member(company_id=company_pk, user_id=request.user.id)
        account = get_object_or_404(
            AmazonAccounts,
            marketplace_id=market_pk,
            user_id=request.user.id,
            company_id=company_pk,
            is_active=True,
        )

        try:

            amazonorder = AmazonOrder.objects.filter(
                amazonaccounts_id=account.id
            )
            amazonorder.delete()

            emailqueue = EmailQueue.objects.filter(
                emailcampaign__amazonmarketplace_id=account.marketplace.id,
                emailcampaign__company_id=company_pk,
            )
            emailqueue.delete()

            emailcampaign = EmailCampaign.objects.filter(
                amazonmarketplace_id=account.marketplace.id,
                company_id=company_pk,
            )
            emailcampaign.delete()

            account.delete()

            # Add the quota back for this feature
            feature = get_feature_by_quota_code(
                company, codename=QUOTA_CODE_MARKETPLACES
            )
            if feature.consumption >= 0:
                feature.consumption = feature.consumption + 1
                feature.save()

        except Exception:
            return Response(
                {"detail": _("Can't disconnect account.")},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        return Response(
            {"detail": _("Account disconnected.")}, status=status.HTTP_200_OK
        )


class AmazonCompanyViewSet(
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = AmazonCompany.objects.all()
    serializer_class = serializers.AmazonCompanySerializer
    permission_classes = (IsAuthenticated,)

    def filter_queryset(self, queryset):
        request = self.request
        kwargs = request.resolver_match.kwargs
        company_pk = kwargs.get("company_pk", kwargs.get("pk", None))
        _member = get_member(company_id=company_pk, user_id=request.user.id)
        queryset = super().filter_queryset(queryset)
        return queryset.filter(
            amazonaccounts__user_id=request.user.id,
            amazonaccounts__company_id=company_pk,
        )


class TestAmazonClientCatalog(View):
    def get(self, request, **kwargs):

        amazonaccount = AmazonAccounts.objects.get(pk=34)
        data = ""
        # Get is_amazon_review_request_allowed via Solicitations
        # solicitations = get_solicitation(amazonaccount)
        # data = send_amazon_review_request(
        #     solicitations, amazonaccount.marketplace, "204-5979728-4185964"
        # )

        # Get Messages action and opt out status for order
        # messaging = get_messaging(amazonaccount)
        # data = get_order_messaging_actions(messaging, "206-8430629-9049145")

        # Temporary files
        timestamp = datetime.timestamp(datetime.now())
        tmp_dir = tempfile.TemporaryDirectory()
        tmp_csv_file_path = (
            tmp_dir.name + "/feedback_report" + str(timestamp) + ".csv"
        )

        report_file = open(tmp_csv_file_path, "w+")

        start_time = (datetime.utcnow() - timedelta(days=25)).isoformat()
        end_time = (datetime.utcnow()).isoformat()

        # get report data (report api call)
        is_done = get_amazon_report(
            amazonaccount,
            ReportType.GET_SELLER_FEEDBACK_DATA,
            report_file,
            start_time,
            end_time,
        )

        # read report data from files
        # report_csv = open(tmp_csv_file_path, "r")

        # print(report_csv.read())

        return HttpResponse(str(data))
