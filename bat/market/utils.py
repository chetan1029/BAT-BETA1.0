import time
from urllib.parse import urlencode

import requests
from django.conf import settings
from sp_api.base import Marketplaces

from bat.autoemail.models import (
    EmailCampaign,
    EmailTemplate,
    GlobalEmailCampaign,
    GlobalEmailTemplate,
)
from bat.company.models import Company
from bat.market.amazon_sp_api.amazon_sp_api import (
    Messaging,
    Reports,
    Solicitations,
)
from bat.market.constants import MARKETPLACE_CODES
from bat.market.models import AmazonCompany


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
            return (
                False,
                {"code": response.status_code, "data": response.json()},
            )


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
            amazonmarketplace_id=marketplace.id
        )
        all_global_email_templates = GlobalEmailTemplate.objects.all()

        if (
            all_global_email_campaigns_of_marketplace.exists()
            and all_global_email_templates.exists()
        ):
            email_campaign_objects = []
            created_templates_id = []
            for (
                global_email_campaigns
            ) in all_global_email_campaigns_of_marketplace:
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


def set_default_amazon_company(company, amazonaccounts):
    """
    copy Company detail to Amazon Company detail.
    """
    if isinstance(company, Company):
        template_data = {}
        template_data["store_name"] = company.name
        template_data["name"] = company.name
        template_data["email"] = company.email
        template_data["phone_number"] = company.phone_number
        template_data["organization_number"] = company.organization_number
        template_data["address1"] = company.address1
        template_data["address2"] = company.address2
        template_data["zip"] = company.zip
        template_data["city"] = company.city
        template_data["region"] = company.region
        template_data["country"] = company.country
        template_data["amazonaccounts"] = amazonaccounts

        AmazonCompany.objects.update_or_create(**template_data)


def get_amazon_report(
    amazonaccount,
    reportType,
    report_file,
    dataStartTime,
    dataEndTime=None,
    marketplaceIds=None,
):
    credentails = amazonaccount.credentails
    marketplace = amazonaccount.marketplace

    kw_args = {"reportType": reportType, "dataStartTime": dataStartTime}
    if marketplaceIds:
        kw_args["marketplaceIds"] = marketplaceIds
    else:
        kw_args["marketplaceIds"] = [marketplace.marketplaceId]

    if dataEndTime:
        kw_args["dataEndTime"] = dataEndTime

    response_1 = Reports(
        marketplace=Marketplaces[
            MARKETPLACE_CODES.get(marketplace.marketplaceId)
        ],
        refresh_token=credentails.refresh_token,
        credentials={
            "refresh_token": credentails.refresh_token,
            "lwa_app_id": settings.LWA_CLIENT_ID,
            "lwa_client_secret": settings.LWA_CLIENT_SECRET,
            "aws_access_key": settings.SP_AWS_ACCESS_KEY_ID,
            "aws_secret_key": settings.SP_AWS_SECRET_ACCESS_KEY,
            "role_arn": settings.ROLE_ARN,
        },
    ).create_report(**kw_args)

    reportId = int(response_1.payload["reportId"])

    iteration = 1
    response_2_payload = {}
    while response_2_payload.get("processingStatus", None) != "DONE":
        response_2 = Reports(
            marketplace=Marketplaces[
                MARKETPLACE_CODES.get(marketplace.marketplaceId)
            ],
            refresh_token=credentails.refresh_token,
            credentials={
                "refresh_token": credentails.refresh_token,
                "lwa_app_id": settings.LWA_CLIENT_ID,
                "lwa_client_secret": settings.LWA_CLIENT_SECRET,
                "aws_access_key": settings.SP_AWS_ACCESS_KEY_ID,
                "aws_secret_key": settings.SP_AWS_SECRET_ACCESS_KEY,
                "role_arn": settings.ROLE_ARN,
            },
        ).get_report(reportId)

        response_2_payload = response_2.payload

        if response_2_payload.get("processingStatus", None) != "DONE":
            time.sleep(30)
        if response_2_payload.get("processingStatus", None) in [
            "CANCELLED",
            "FATAL",
        ]:
            return False
        iteration = iteration + 1
        if iteration > 10:
            break

    Reports(
        marketplace=Marketplaces[
            MARKETPLACE_CODES.get(marketplace.marketplaceId)
        ],
        refresh_token=credentails.refresh_token,
        credentials={
            "refresh_token": credentails.refresh_token,
            "lwa_app_id": settings.LWA_CLIENT_ID,
            "lwa_client_secret": settings.LWA_CLIENT_SECRET,
            "aws_access_key": settings.SP_AWS_ACCESS_KEY_ID,
            "aws_secret_key": settings.SP_AWS_SECRET_ACCESS_KEY,
            "role_arn": settings.ROLE_ARN,
        },
    ).get_report_document(
        response_2_payload["reportDocumentId"], decrypt=True, file=report_file
    )

    return True


def get_messaging(amazonaccount):
    """Get messaging object."""
    credentails = amazonaccount.credentails
    marketplace = amazonaccount.marketplace
    messaging = Messaging(
        marketplace=Marketplaces[
            MARKETPLACE_CODES.get(marketplace.marketplaceId)
        ],
        refresh_token=credentails.refresh_token,
        credentials={
            "refresh_token": credentails.refresh_token,
            "lwa_app_id": settings.LWA_CLIENT_ID,
            "lwa_client_secret": settings.LWA_CLIENT_SECRET,
            "aws_access_key": settings.SP_AWS_ACCESS_KEY_ID,
            "aws_secret_key": settings.SP_AWS_SECRET_ACCESS_KEY,
            "role_arn": settings.ROLE_ARN,
        },
    )
    return messaging


def get_order_messaging_actions(messaging, order_id):
    """Get order messging action in a list and save them with order."""
    message_data = messaging.get_messaging_actions_for_order(order_id)

    actions = []
    links = message_data.kwargs["_links"]["actions"]
    for link in links:
        actions.append(link["name"])

    is_optout = False
    if ("negativeFeedbackRemoval" not in actions) and (
        "sendInvoice" not in actions
    ):
        is_optout = True

    return {"actions": actions, "is_optout": is_optout}


def get_solicitation(amazonaccount):
    """Get solicitations object."""
    credentails = amazonaccount.credentails
    marketplace = amazonaccount.marketplace
    solicitations = Solicitations(
        marketplace=Marketplaces[
            MARKETPLACE_CODES.get(marketplace.marketplaceId)
        ],
        refresh_token=credentails.refresh_token,
        credentials={
            "refresh_token": credentails.refresh_token,
            "lwa_app_id": settings.LWA_CLIENT_ID,
            "lwa_client_secret": settings.LWA_CLIENT_SECRET,
            "aws_access_key": settings.SP_AWS_ACCESS_KEY_ID,
            "aws_secret_key": settings.SP_AWS_SECRET_ACCESS_KEY,
            "role_arn": settings.ROLE_ARN,
        },
    )
    return solicitations


def send_amazon_review_request(solicitations, marketplace, order_id):
    """Get order messging action in a list and save them with order."""
    status = False
    solicitations_data = solicitations.get_solicitation_actions_for_order(
        order_id
    )

    actions = []
    links = solicitations_data.kwargs["_links"]["actions"]
    for link in links:
        actions.append(link["name"])

    is_amazon_review_request_allowed = False
    if "productReviewAndSellerFeedback" in actions:
        is_amazon_review_request_allowed = True

    if is_amazon_review_request_allowed:
        # send amazon product review and feedback request if its allowed for order.
        solicitations.create_productreview_and_sellerfeedback_solicitation(
            order_id, marketplaceIds=[marketplace.marketplaceId]
        )
        status = True
    return status
