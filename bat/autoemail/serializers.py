import datetime

from rest_framework import serializers

from bat.autoemail.constants import (
    BUYER_PURCHASE_CHOICES,
    CHANNEL_CHOICES,
    EMAIL_CAMPAIGN_STATUS_CHOICE,
    EXCLUDE_ORDERS_CHOICES,
    ORDER_EMAIL_STATUS_QUEUED,
    ORDER_EMAIL_STATUS_SCHEDULED,
    ORDER_EMAIL_STATUS_SEND,
)
from bat.autoemail.models import EmailCampaign, EmailQueue, EmailTemplate
from bat.globalutils.utils import get_status_object
from bat.market.constants import AMAZON_ORDER_STATUS_CHOICE
from bat.market.serializers import AmazonMarketplaceSerializer
from bat.serializersFields.serializers_fields import StatusField


class EmailTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailTemplate
        fields = (
            "id",
            "name",
            "subject",
            "default_cc",
            "logo",
            "attachment_file",
            "language",
            "template",
            "slug",
            "company",
            "is_active",
            "extra_data",
        )
        read_only_fields = ("id", "slug", "company", "is_active", "extra_data")


class EmailCampaignSerializer(serializers.ModelSerializer):
    status = StatusField(choices=EMAIL_CAMPAIGN_STATUS_CHOICE)
    order_status = StatusField(choices=AMAZON_ORDER_STATUS_CHOICE, required=True)
    emailtemplate = EmailTemplateSerializer(read_only=True)
    amazonmarketplace = AmazonMarketplaceSerializer(read_only=True)
    channel = serializers.MultipleChoiceField(choices=CHANNEL_CHOICES)
    buyer_purchase_count = serializers.MultipleChoiceField(
        choices=BUYER_PURCHASE_CHOICES
    )
    exclude_orders = serializers.MultipleChoiceField(
        choices=EXCLUDE_ORDERS_CHOICES
    )

    email_sent = serializers.SerializerMethodField()
    email_in_queue = serializers.SerializerMethodField()
    last_email_send_in_queue = serializers.SerializerMethodField()
    email_sent_today = serializers.SerializerMethodField()
    email_queue_today = serializers.SerializerMethodField()

    class Meta:
        model = EmailCampaign
        fields = (
            "id",
            "name",
            "emailtemplate",
            "status",
            "amazonmarketplace",
            "order_status",
            "channel",
            "schedule",
            "schedule_time",
            "schedule_days",
            "buyer_purchase_count",
            "exclude_orders",
            "company",
            "extra_data",
            "email_sent",
            "last_email_send_in_queue",
            "include_invoice",
            "email_in_queue",
            "email_sent_today",
            "email_queue_today",
        )
        read_only_fields = ("id", "amazonmarketplace", "company")

    def get_email_sent(self, obj):
        return EmailQueue.objects.filter(
            emailcampaign_id=obj.id, status__name=ORDER_EMAIL_STATUS_SEND
        ).count()

    def get_email_in_queue(self, obj):
        return EmailQueue.objects.filter(
            emailcampaign_id=obj.id,
            status__name__in=[
                ORDER_EMAIL_STATUS_SCHEDULED,
                ORDER_EMAIL_STATUS_QUEUED,
            ],
        ).count()

    def get_last_email_send_in_queue(self, obj):
        last_email = (
            EmailQueue.objects.filter(
                emailcampaign_id=obj.id, status__name=ORDER_EMAIL_STATUS_SEND
            )
            .order_by("-send_date")
            .first()
        )
        if last_email:
            return last_email.send_date
        return None

    def update(self, instance, validated_data):
        if self.partial:
            if validated_data.get("status", None):
                validated_data["status"] = get_status_object(validated_data)
            if validated_data.get("order_status", None):
                validated_data["order_status"] = get_status_object(
                    validated_data, status_field="order_status")
        else:
            validated_data["status"] = get_status_object(validated_data)
            validated_data["order_status"] = get_status_object(
                validated_data, status_field="order_status")
        return super().update(instance, validated_data)

    def get_email_sent_today(self, obj):
        today = datetime.date.today()
        return EmailQueue.objects.filter(
            emailcampaign_id=obj.id,
            status__name=ORDER_EMAIL_STATUS_SEND,
            send_date__year=today.year,
            send_date__month=today.month,
            send_date__day=today.day,
        ).count()

    def get_email_queue_today(self, obj):
        today = datetime.date.today()
        return EmailQueue.objects.filter(
            emailcampaign_id=obj.id,
            status__name=ORDER_EMAIL_STATUS_SEND,
            create_date__year=today.year,
            create_date__month=today.month,
            create_date__day=today.day,
        ).count()


class EmailQueueSerializer(serializers.ModelSerializer):
    status = StatusField(choices=ORDER_EMAIL_STATUS_SCHEDULED)

    class Meta:
        model = EmailQueue
        fields = (
            "id",
            "amazonorder",
            "emailcampaign",
            "sent_to",
            "sent_from",
            "subject",
            "template",
            "status",
            "schedule_date",
            "extra_data",
        )
        read_only_fields = (
            "id",
            "amazonorder",
            "emailcampaign",
            "sent_to",
            "sent_from",
            "subject",
            "template",
            "status",
            "schedule_date",
            "extra_data",
        )


class TestEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
