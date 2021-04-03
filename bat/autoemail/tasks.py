"""Task that can run by celery will be placed here."""
from celery.utils.log import get_task_logger
from config.celery import app
from datetime import datetime, timedelta


from django.conf import settings

from bat.market.models import (
    AmazonOrder,
    AmazonAccounts
)
from bat.autoemail.models import EmailQueue, EmailCampaign
from bat.autoemail.constants import (
    ORDER_EMAIL_PARENT_STATUS,
    ORDER_EMAIL_STATUS_QUEUED,
    ORDER_EMAIL_STATUS_SEND,
    ORDER_EMAIL_STATUS_SCHEDULED)
from bat.setting.utils import get_status


logger = get_task_logger(__name__)


@app.task
def add_order_email_in_queue(amazon_order_id, email_campaign_id):
    order = AmazonOrder.objects.get(pk=amazon_order_id)
    email_campaign = EmailCampaign.objects.get(pk=email_campaign_id)

    email_queue_data = {}
    email_queue_data["amazonorder"] = order
    email_queue_data["emailcampaign"] = email_campaign
    # email_queue_data["sent_to"] = order.buyer_email
    email_queue_data["sent_to"] = "chetan@volutz.com"
    email_queue_data["sent_from"] = settings.MAIL_FROM_ADDRESS
    email_queue_data["subject"] = email_campaign.emailtemplate.subject
    email_queue_data["template"] = email_campaign.emailtemplate
    email_queue_data["status"] = get_status(ORDER_EMAIL_PARENT_STATUS, ORDER_EMAIL_STATUS_QUEUED)
    email_queue_data["schedule_date"] = datetime.utcnow(
    ) - timedelta(days=email_campaign.schedule_days)

    EmailQueue.objects.create(**email_queue_data)


@app.task
def send_email(email_queue_id):
    email_queue = EmailQueue.objects.get(pk=email_queue_id)
    email_queue.send_mail()
    email_queue.status = get_status(ORDER_EMAIL_PARENT_STATUS, ORDER_EMAIL_STATUS_SEND)
    email_queue.save()


@app.task
def send_email_from_queue():
    queued_emails = EmailQueue.objects.filter(
        status__name=ORDER_EMAIL_STATUS_QUEUED,
        schedule_date__lte=datetime.utcnow(
        ))

    for email in queued_emails:
        send_email.delay(email.id)

    EmailQueue.objects.filter(
        status__name=ORDER_EMAIL_STATUS_QUEUED,
        schedule_date__lte=datetime.utcnow(
        )).update(status=get_status(ORDER_EMAIL_PARENT_STATUS, ORDER_EMAIL_STATUS_SCHEDULED))


@app.task
def email_queue_create_for_orders(amazonaccount_id, amazon_created_orders_pk, amazon_updated_orders_pk, amazon_orders_old_status_map):

    amazonaccount = AmazonAccounts.objects.get(pk=amazonaccount_id)

    amazon_updated_orders = AmazonOrder.objects.filter(
        id__in=amazon_updated_orders_pk).values_list("id", "status__name")
    amazon_orders_new_status_map = {str(k): v for k, v in amazon_updated_orders}

    amazon_created_orders = AmazonOrder.objects.filter(
        id__in=amazon_created_orders_pk).values_list("id", "status__name")
    amazon_created_orders_status_map = {str(k): v for k, v in amazon_created_orders}

    email_campaigns = EmailCampaign.objects.filter(
        amazonmarketplace=amazonaccount.marketplace, company=amazonaccount.company).values_list("order_status__name", "id")

    email_campaigns_map = {}
    for k, v in email_campaigns:
        email_campaigns_map.setdefault(k, []).append(v)

    for pk in amazon_updated_orders_pk:
        pk = str(pk)
        if amazon_orders_new_status_map[pk] != amazon_orders_old_status_map[pk]:
            email_campaigns_with_status = email_campaigns_map.get(
                amazon_orders_new_status_map[pk], [])
            for email_campaign_pk in email_campaigns_with_status:
                add_order_email_in_queue.delay(pk, email_campaign_pk)

    for order_pk in amazon_created_orders_pk:
        object_pk = str(object_pk)
        email_campaigns_with_status = email_campaigns_map.get(
            amazon_created_orders_status_map[order_pk], [])
        for email_campaign_pk in email_campaigns_with_status:
            add_order_email_in_queue.delay(order_pk, email_campaign_pk)
