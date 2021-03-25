from django.conf import settings

import requests
from urllib.parse import urlencode

from bat.autoemail.models import (
    EmailCampaign,
    EmailTemplate,
    GlobalEmailCampaign,
    GlobalEmailTemplate,
)

from bat.company.models import Company


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
