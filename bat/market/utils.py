import time

from django.conf import settings

from sp_api.base import Marketplaces

import requests
from urllib.parse import urlencode

from bat.autoemail.models import (
    EmailCampaign,
    EmailTemplate,
    GlobalEmailCampaign,
    GlobalEmailTemplate,
)

from bat.company.models import Company
from bat.market.amazon_sp_api.amazon_sp_api import Reports
from bat.market.constants import MARKETPLACE_CODES


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


def set_default_email_campaign_templates(company, marketplace):
    """
    copy global email campaigns, and global email templates to given company's campaigns and email templates.
    """
    if isinstance(company, Company):

        def _get_kwargs_for_template(company, global_template):
            template_data = {}
            template_data["company"] = company
            template_data["name"] = global_template.name
            template_data["subject"] = global_template.subject
            template_data["default_cc"] = global_template.default_cc
            template_data["language"] = global_template.language
            template_data["template"] = global_template.template
            return template_data

        all_global_email_campaigns_of_marketplace = GlobalEmailCampaign.objects.filter(
            amazonmarketplace_id=marketplace.id)
        all_global_email_templates = GlobalEmailTemplate.objects.all()

        if (
            all_global_email_campaigns_of_marketplace.exists()
            and all_global_email_templates.exists()
        ):
            email_campaign_objects = []
            created_templates_id = []
            for global_email_campaigns in all_global_email_campaigns_of_marketplace:
                data = {}
                data["company"] = company
                data["name"] = global_email_campaigns.name
                data["status"] = global_email_campaigns.status
                data[
                    "amazonmarketplace"
                ] = global_email_campaigns.amazonmarketplace
                data["order_status"] = global_email_campaigns.order_status
                data["channel"] = global_email_campaigns.channel
                data["schedule"] = global_email_campaigns.schedule
                data["schedule_days"] = global_email_campaigns.schedule_days
                data[
                    "buyer_purchase_count"
                ] = global_email_campaigns.buyer_purchase_count
                data["exclude_orders"] = global_email_campaigns.exclude_orders
                data["extra_data"] = global_email_campaigns.extra_data

                # copy email template
                template_data = {}
                global_template = all_global_email_templates.get(
                    pk=global_email_campaigns.emailtemplate_id
                )
                template_data = _get_kwargs_for_template(
                    company, global_template
                )
                template = EmailTemplate.objects.create(**template_data)
                created_templates_id.append(
                    global_email_campaigns.emailtemplate_id
                )

                data["emailtemplate"] = template
                email_campaign_objects.append(EmailCampaign(**data))

            EmailCampaign.objects.bulk_create(email_campaign_objects)


def get_amazon_report(amazonaccount, reportType, report_file, dataStartTime, dataEndTime=None, marketplaceIds=None):
    credentails = amazonaccount.credentails
    marketplace = amazonaccount.marketplace

    kw_args = {"reportType": reportType,
               "dataStartTime": dataStartTime
               }
    if marketplaceIds:
        kw_args["marketplaceIds"] = marketplaceIds
    else:
        kw_args["marketplaceIds"] = [marketplace.marketplaceId]

    if dataEndTime:
        kw_args["dataEndTime"] = dataEndTime

    response_1 = Reports(
        marketplace=Marketplaces[MARKETPLACE_CODES.get(marketplace.marketplaceId)],
        refresh_token=credentails.refresh_token,
        credentials={
            "refresh_token": credentails.refresh_token,
            "lwa_app_id": settings.LWA_CLIENT_ID,
            "lwa_client_secret": settings.LWA_CLIENT_SECRET,
            "aws_access_key": settings.SP_AWS_ACCESS_KEY_ID,
            "aws_secret_key": settings.SP_AWS_SECRET_ACCESS_KEY,
            "role_arn": settings.ROLE_ARN,
        }
    ).create_report(**kw_args)

    reportId = int(response_1.payload["reportId"])

    iteration = 1
    response_2_payload = {}
    while response_2_payload.get("processingStatus", None) != "DONE":
        response_2 = Reports(
            marketplace=Marketplaces[MARKETPLACE_CODES.get(marketplace.marketplaceId)],
            refresh_token=credentails.refresh_token,
            credentials={
                "refresh_token": credentails.refresh_token,
                "lwa_app_id": settings.LWA_CLIENT_ID,
                "lwa_client_secret": settings.LWA_CLIENT_SECRET,
                "aws_access_key": settings.SP_AWS_ACCESS_KEY_ID,
                "aws_secret_key": settings.SP_AWS_SECRET_ACCESS_KEY,
                "role_arn": settings.ROLE_ARN,
            }
        ).get_report(reportId)
        response_2_payload = response_2.payload
        if response_2_payload.get("processingStatus", None) != "DONE":
            time.sleep(10)
        iteration = iteration + 1
        if(iteration > 10):
            break

    Reports(
        marketplace=Marketplaces[MARKETPLACE_CODES.get(marketplace.marketplaceId)],
        refresh_token=credentails.refresh_token,
        credentials={
            "refresh_token": credentails.refresh_token,
            "lwa_app_id": settings.LWA_CLIENT_ID,
            "lwa_client_secret": settings.LWA_CLIENT_SECRET,
            "aws_access_key": settings.SP_AWS_ACCESS_KEY_ID,
            "aws_secret_key": settings.SP_AWS_SECRET_ACCESS_KEY,
            "role_arn": settings.ROLE_ARN,
        },
    ).get_report_document(response_2_payload["reportDocumentId"], decrypt=True, file=report_file)
