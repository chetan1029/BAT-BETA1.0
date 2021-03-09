from rest_framework import serializers

from bat.serializersFields.serializers_fields import StatusField
from bat.autoemail.models import EmailCampaign, EmailQueue
from bat.autoemail.constants import (
    BUYER_PURCHASE_CHOICES,
    CHANNEL_CHOICES,
    EXCLUDE_ORDERS_CHOICES,
    ORDER_EMAIL_STATUS_QUEUED,
    ORDER_EMAIL_STATUS_SEND,
    ORDER_EMAIL_STATUS_SHEDULED,
)
from bat.market.serializers import AmazonMarketplaceSerializer
from bat.globalutils.utils import get_status_object


class EmailCampaignSerializer(serializers.ModelSerializer):
    status = StatusField()
    order_status = StatusField()
    amazonmarketplace = AmazonMarketplaceSerializer(read_only=True)
    channel = serializers.MultipleChoiceField(choices=CHANNEL_CHOICES)
    buyer_purchase_count = serializers.MultipleChoiceField(choices=BUYER_PURCHASE_CHOICES)
    exclude_orders = serializers.MultipleChoiceField(choices=EXCLUDE_ORDERS_CHOICES)

    email_sent = serializers.SerializerMethodField()
    email_in_queue = serializers.SerializerMethodField()

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
            "email_in_queue",
        )
        read_only_fields = ("id", "amazonmarketplace", "company",)

    def get_email_sent(self, obj):
        return EmailQueue.objects.filter(emailcampaign_id=obj.id, status__name=ORDER_EMAIL_STATUS_SEND).count()

    def get_email_in_queue(self, obj):
        return EmailQueue.objects.filter(
            emailcampaign_id=obj.id,
            status__name__in=[ORDER_EMAIL_STATUS_SHEDULED, ORDER_EMAIL_STATUS_QUEUED]
        ).count()

    def update(self, instance, validated_data):
        validated_data["status"] = get_status_object(validated_data)
        validated_data["order_status"] = get_status_object(
            validated_data, status_field="order_status")
        return super().update(instance, validated_data)


class EmailQueueSerializer(serializers.ModelSerializer):
    status = StatusField(choices=ORDER_EMAIL_STATUS_SHEDULED)

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
