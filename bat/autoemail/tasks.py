"""Task that can run by celery will be placed here."""
import time
from datetime import datetime, timedelta

import pytz
from celery.utils.log import get_task_logger
from django.conf import settings
from django.db.models import F

from bat.autoemail.constants import (
    AS_SOON_AS,
    DAILY,
    EMAIL_CAMPAIGN_PARENT_STATUS,
    EMAIL_CAMPAIGN_STATUS_ACTIVE,
    ORDER_EMAIL_PARENT_STATUS,
    ORDER_EMAIL_STATUS_OPTOUT,
    ORDER_EMAIL_STATUS_QUEUED,
    ORDER_EMAIL_STATUS_SCHEDULED,
    ORDER_EMAIL_STATUS_SEND,
)
from bat.autoemail.models import EmailCampaign, EmailQueue
from bat.market.models import AmazonAccounts, AmazonOrder
from bat.market.utils import (
    get_messaging,
    get_order_messaging_actions,
    get_solicitation,
    send_amazon_review_request,
)
from bat.setting.utils import get_status
from bat.subscription.constants import (
    QUOTA_CODE_AMAZON_AUTOMATIC_REVIEW_REQUEST,
    QUOTA_CODE_MARKETPLACES_FREE_EMAIL,
)
from bat.subscription.utils import get_feature_by_quota_code
from config.celery import app

logger = get_task_logger(__name__)


@app.task
def add_order_email_in_queue(amazon_order_id, email_campaign_id):
    order = AmazonOrder.objects.get(pk=amazon_order_id)
    email_campaign = EmailCampaign.objects.get(pk=email_campaign_id)

    sent_from = settings.MAIL_FROM_ADDRESS
    if order.amazonaccounts.credentails.email:
        sent_from = order.amazonaccounts.credentails.email

    email_queue_data = {}
    email_queue_data["amazonorder"] = order
    email_queue_data["emailcampaign"] = email_campaign
    email_queue_data["sent_to"] = order.buyer_email
    email_queue_data["sent_from"] = sent_from
    email_queue_data["subject"] = email_campaign.emailtemplate.subject
    email_queue_data["template"] = email_campaign.emailtemplate
    email_queue_data["status"] = get_status(
        ORDER_EMAIL_PARENT_STATUS, ORDER_EMAIL_STATUS_QUEUED
    )

    if email_campaign.schedule == AS_SOON_AS:
        email_queue_data["schedule_date"] = datetime.utcnow()
    else:
        day_diff = (
            email_campaign.schedule_days
            - (
                datetime.utcnow().replace(tzinfo=pytz.UTC)
                - order.reporting_date
            ).days
        )
        if day_diff <= 0:
            email_queue_data["schedule_date"] = datetime.utcnow()
        else:
            email_queue_data["schedule_date"] = datetime.utcnow() + timedelta(
                days=day_diff
            )

    EmailQueue.objects.create(**email_queue_data)


@app.task
def add_initial_order_email_in_queue(amazon_order_id, email_campaign_id):
    order = AmazonOrder.objects.get(pk=amazon_order_id)
    email_campaign = EmailCampaign.objects.get(pk=email_campaign_id)

    sent_from = settings.MAIL_FROM_ADDRESS
    if order.amazonaccounts.credentails.email:
        sent_from = order.amazonaccounts.credentails.email

    email_queue_data = {}
    email_queue_data["amazonorder"] = order
    email_queue_data["emailcampaign"] = email_campaign
    email_queue_data["sent_to"] = order.buyer_email
    email_queue_data["sent_from"] = sent_from
    email_queue_data["subject"] = email_campaign.emailtemplate.subject
    email_queue_data["template"] = email_campaign.emailtemplate
    email_queue_data["status"] = get_status(
        ORDER_EMAIL_PARENT_STATUS, ORDER_EMAIL_STATUS_QUEUED
    )

    if email_campaign.schedule == AS_SOON_AS:
        email_queue_data["schedule_date"] = datetime.utcnow()
    else:

        day_diff = (
            email_campaign.schedule_days
            - (
                datetime.utcnow().replace(tzinfo=pytz.UTC)
                - order.reporting_date
            ).days
        )
        if day_diff <= 0:
            email_queue_data["schedule_date"] = datetime.utcnow()
        else:
            email_queue_data["schedule_date"] = datetime.utcnow() + timedelta(
                days=day_diff
            )

    EmailQueue.objects.create(**email_queue_data)


@app.task
def send_email(email_queue_id):

    # email_queue = EmailQueue.objects.get(pk=email_queue_id)
    email_queue = EmailQueue.objects.get(
        amazonorder__order_id="114-8601112-6451448"
    )
    feature = get_feature_by_quota_code(
        email_queue.get_company(), codename=QUOTA_CODE_MARKETPLACES_FREE_EMAIL
    )

    feature_opt_out = get_feature_by_quota_code(
        email_queue.get_company(),
        codename=QUOTA_CODE_AMAZON_AUTOMATIC_REVIEW_REQUEST,
    )

    # check for opt out order
    amazonaccount = email_queue.amazonorder.amazonaccounts

    messaging = get_messaging(amazonaccount)
    logger.info("Amazon order ID " + str(email_queue.amazonorder.order_id))
    time.sleep(1)
    message_action = get_order_messaging_actions(
        messaging, email_queue.amazonorder.order_id
    )
    if message_action["is_optout"]:
        email_queue.amazonorder.opt_out = True
        email_queue.amazonorder.save()
        email_queue.status = get_status(
            ORDER_EMAIL_PARENT_STATUS, ORDER_EMAIL_STATUS_OPTOUT
        )
        if (
            not email_queue.amazonorder.amazon_review
            and email_queue.emailcampaign.send_optout
            and feature_opt_out.consumption > 0
        ):
            solicitations = get_solicitation(amazonaccount)
            amazon_review_request_status = send_amazon_review_request(
                solicitations,
                amazonaccount.marketplace,
                email_queue.amazonorder.order_id,
            )
            email_queue.amazonorder.amazon_review = (
                amazon_review_request_status
            )
        email_queue.save()

    else:
        if feature.consumption > 0:
            email_queue.send_mail()
            logger.info("send email here")
            email_queue.status = get_status(
                ORDER_EMAIL_PARENT_STATUS, ORDER_EMAIL_STATUS_SEND
            )
            email_queue.send_date = datetime.utcnow()
            email_queue.save()
            feature.consumption = (
                feature.consumption
                - email_queue.emailcampaign.get_charged_points()
            )
            feature.save()


@app.task
def send_email_from_queue():
    current_time = datetime.utcnow()
    queued_emails = EmailQueue.objects.filter(
        status__name=ORDER_EMAIL_STATUS_QUEUED,
        schedule_date__lte=current_time,
        emailcampaign__status__name=EMAIL_CAMPAIGN_STATUS_ACTIVE,
        amazonorder__purchase_date__gte=F("emailcampaign__activation_date"),
    )[:50]

    for email in queued_emails:
        send_email.delay(email.id)

    EmailQueue.objects.filter(
        status__name=ORDER_EMAIL_STATUS_QUEUED,
        schedule_date__lte=current_time,
        emailcampaign__status__name=EMAIL_CAMPAIGN_STATUS_ACTIVE,
        amazonorder__purchase_date__gte=F("emailcampaign__activation_date"),
    ).update(
        status=get_status(
            ORDER_EMAIL_PARENT_STATUS, ORDER_EMAIL_STATUS_SCHEDULED
        )
    )


@app.task
def email_queue_create_for_orders(
    amazonaccount_id,
    amazon_created_orders_pk,
    amazon_updated_orders_pk,
    amazon_orders_old_status_map,
):

    amazonaccount = AmazonAccounts.objects.get(pk=amazonaccount_id)

    amazon_updated_orders = AmazonOrder.objects.filter(
        id__in=amazon_updated_orders_pk
    ).values_list("id", "status__name")
    amazon_orders_new_status_map = {
        str(k): v for k, v in amazon_updated_orders
    }

    amazon_created_orders = AmazonOrder.objects.filter(
        id__in=amazon_created_orders_pk
    ).values_list("id", "status__name")
    amazon_created_orders_status_map = {
        str(k): v for k, v in amazon_created_orders
    }

    email_campaigns = EmailCampaign.objects.filter(
        amazonmarketplace=amazonaccount.marketplace,
        company=amazonaccount.company,
    ).values_list("order_status__name", "id")

    email_campaigns_map = {}
    for k, v in email_campaigns:
        email_campaigns_map.setdefault(k, []).append(v)

    for pk in amazon_updated_orders_pk:
        pk = str(pk)
        if (
            amazon_orders_new_status_map[pk]
            != amazon_orders_old_status_map[pk]
        ):
            email_campaigns_with_status = email_campaigns_map.get(
                amazon_orders_new_status_map[pk], []
            )
            for email_campaign_pk in email_campaigns_with_status:
                add_order_email_in_queue.delay(pk, email_campaign_pk)

    for order_pk in amazon_created_orders_pk:
        order_pk = str(order_pk)
        email_campaigns_with_status = email_campaigns_map.get(
            amazon_created_orders_status_map[order_pk], []
        )
        for email_campaign_pk in email_campaigns_with_status:
            add_order_email_in_queue.delay(order_pk, email_campaign_pk)


@app.task
def email_queue_create_for_initial_orders(
    amazonaccount_id, amazon_created_orders_pk
):
    amazonaccount = AmazonAccounts.objects.get(pk=amazonaccount_id)

    amazon_created_orders = AmazonOrder.objects.filter(
        id__in=amazon_created_orders_pk
    ).values_list("id", "status__name")
    amazon_created_orders_status_map = {
        str(k): v for k, v in amazon_created_orders
    }

    email_campaigns = EmailCampaign.objects.filter(
        amazonmarketplace=amazonaccount.marketplace,
        company=amazonaccount.company,
    ).values_list("order_status__name", "id")

    email_campaigns_map = {}
    for k, v in email_campaigns:
        email_campaigns_map.setdefault(k, []).append(v)

    for order_pk in amazon_created_orders_pk:
        order_pk = str(order_pk)
        email_campaigns_with_status = email_campaigns_map.get(
            amazon_created_orders_status_map[order_pk], []
        )
        for email_campaign_pk in email_campaigns_with_status:
            add_order_email_in_queue.delay(order_pk, email_campaign_pk)


@app.task
def email_queue_create_for_new_campaign(email_campaign_id):
    email_campaign = EmailCampaign.objects.get(pk=email_campaign_id)
    orders = AmazonOrder.objects.filter(
        purchase_date__gte=email_campaign.activation_date,
        status=email_campaign.order_status,
        amazonaccounts__marketplace=email_campaign.amazonmarketplace,
        amazonaccounts__company=email_campaign.company,
    )
    if orders.exists():
        for order in orders:
            add_order_email_in_queue.delay(order.id, email_campaign.id)
