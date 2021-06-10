import datetime

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from bat.autoemail.constants import (
    BUYER_PURCHASE_CHOICES,
    CHANNEL_CHOICES,
    EMAIL_CAMPAIGN_STATUS_CHOICE,
    EXCLUDE_ORDERS_CHOICES,
    ORDER_EMAIL_STATUS_OPTOUT,
    ORDER_EMAIL_STATUS_QUEUED,
    ORDER_EMAIL_STATUS_SCHEDULED,
    ORDER_EMAIL_STATUS_SEND,
)
from bat.autoemail.models import (
    EmailCampaign,
    EmailQueue,
    EmailTemplate,
    GlobalEmailTemplate,
)
from bat.globalutils.utils import get_status_object
from bat.market.constants import AMAZON_ORDER_STATUS_CHOICE
from bat.market.serializers import (
    AmazonMarketplaceSerializerField,
    AmazonOrderSerializer,
)
from bat.serializersFields.serializers_fields import StatusField
from bat.setting.models import Status
from bat.setting.serializers import StatusSerializer


class GlobalEmailTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = GlobalEmailTemplate
        fields = (
            "id",
            "name",
            "subject",
            "default_cc",
            "language",
            "template",
            "slug",
            "is_active",
            "extra_data",
        )
        read_only_fields = ("id", "slug", "company", "is_active", "extra_data")


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


class EmailTemplateSerializerField(serializers.Field):
    def to_representation(self, value):
        """
        give json of Email Template .
        """
        if isinstance(value, EmailTemplate):
            return EmailTemplateSerializer(value).data
        return value

    def to_internal_value(self, data):
        try:
            obj = EmailTemplate.objects.get(pk=data)
            return obj
        except ObjectDoesNotExist:
            raise ValidationError(
                {"emailtemplate": _(f"{data} is not a valid Email Template.")}
            )


class OrderStatusSerializerField(serializers.Field):
    def to_representation(self, value):
        """
        give json of Email Template .
        """
        if isinstance(value, Status):
            return StatusSerializer(value).data
        return value

    def to_internal_value(self, data):
        try:
            obj = Status.objects.get(pk=data)
            return obj
        except ObjectDoesNotExist:
            raise ValidationError(
                {"order_status": _(f"{data} is not a valid Status.")}
            )


class EmailCampaignSerializer(serializers.ModelSerializer):
    status = StatusField(choices=EMAIL_CAMPAIGN_STATUS_CHOICE)
    order_status = OrderStatusSerializerField()
    emailtemplate = EmailTemplateSerializerField()
    amazonmarketplace = AmazonMarketplaceSerializerField()
    channel = serializers.MultipleChoiceField(choices=CHANNEL_CHOICES)
    buyer_purchase_count = serializers.MultipleChoiceField(
        choices=BUYER_PURCHASE_CHOICES
    )
    exclude_orders = serializers.MultipleChoiceField(
        choices=EXCLUDE_ORDERS_CHOICES
    )

    email_sent = serializers.SerializerMethodField()
    email_opt_out = serializers.SerializerMethodField()
    email_in_queue = serializers.SerializerMethodField()
    last_email_send_in_queue = serializers.SerializerMethodField()
    email_sent_today = serializers.SerializerMethodField()
    email_queue_today = serializers.SerializerMethodField()
    email_opt_out_today = serializers.SerializerMethodField()
    opt_out_rate = serializers.SerializerMethodField()

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
            "email_opt_out",
            "last_email_send_in_queue",
            "include_invoice",
            "send_optout",
            "email_in_queue",
            "email_sent_today",
            "email_queue_today",
            "email_opt_out_today",
            "opt_out_rate",
            "activation_date",
        )
        read_only_fields = ("id", "amazonmarketplace", "company")

    def get_email_sent(self, obj):
        return EmailQueue.objects.filter(
            emailcampaign_id=obj.id, status__name=ORDER_EMAIL_STATUS_SEND
        ).count()

    def get_email_opt_out(self, obj):
        return EmailQueue.objects.filter(
            emailcampaign_id=obj.id, status__name=ORDER_EMAIL_STATUS_OPTOUT
        ).count()

    def get_opt_out_rate(self, obj):
        opt_out_rate = 0
        email_opt_out = self.get_email_opt_out(obj)
        if email_opt_out:
            email_sent = self.get_email_sent(obj)
            if email_sent:
                opt_out_rate = round((email_opt_out / email_sent) * 100, 2)
        return opt_out_rate

    def get_email_in_queue(self, obj):
        return EmailQueue.objects.filter(
            emailcampaign_id=obj.id,
            status__name__in=[
                ORDER_EMAIL_STATUS_SCHEDULED,
                ORDER_EMAIL_STATUS_QUEUED,
            ],
            amazonorder__purchase_date__gte=obj.activation_date,
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

    def create(self, validated_data):
        validated_data["status"] = get_status_object(validated_data)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if self.partial:
            if validated_data.get("status", None):
                validated_data["status"] = get_status_object(validated_data)
        else:
            validated_data["status"] = get_status_object(validated_data)
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

    def get_email_opt_out_today(self, obj):
        today = datetime.date.today()
        return EmailQueue.objects.filter(
            emailcampaign_id=obj.id,
            status__name=ORDER_EMAIL_STATUS_OPTOUT,
            send_date__year=today.year,
            send_date__month=today.month,
            send_date__day=today.day,
        ).count()

    def get_email_queue_today(self, obj):
        today = datetime.date.today()
        return EmailQueue.objects.filter(
            emailcampaign_id=obj.id,
            status__name__in=[
                ORDER_EMAIL_STATUS_SCHEDULED,
                ORDER_EMAIL_STATUS_QUEUED,
            ],
            schedule_date__year=today.year,
            schedule_date__month=today.month,
            schedule_date__day=today.day,
            amazonorder__purchase_date__gte=obj.activation_date,
        ).count()

    def validate(self, data):
        """Validate conditions."""
        company_id = self.context.get("company_id", None)
        campaign_id = self.context.get("campaign_id", None)
        user = self.context.get("user", None)
        include_invoice = data.get("include_invoice", None)
        send_optout = data.get("send_optout", None)
        amazonmarketplace_id = data.get("amazonmarketplace", None)

        if campaign_id:
            amazonmarketplace_id = EmailCampaign.objects.get(
                pk=campaign_id
            ).amazonmarketplace_id

        if include_invoice and amazonmarketplace_id:
            if EmailCampaign.objects.filter(
                amazonmarketplace_id=amazonmarketplace_id,
                company_id=company_id,
                include_invoice=True,
            ).exists():
                raise serializers.ValidationError(
                    "You already have Include Invoice for one of your campaign for the same marketplace."
                )

        if send_optout and amazonmarketplace_id:
            if EmailCampaign.objects.filter(
                amazonmarketplace_id=amazonmarketplace_id,
                company_id=company_id,
                send_optout=True,
            ).exists():
                raise serializers.ValidationError(
                    "You already have Opt-out email sending for one of your campaign for the same marketplace."
                )

        return super().validate(data)


class EmailQueueSerializer(serializers.ModelSerializer):
    status = StatusField(choices=ORDER_EMAIL_STATUS_SCHEDULED)
    amazonorder = AmazonOrderSerializer(read_only=True)
    emailcampaign = EmailCampaignSerializer(read_only=True)

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
    campaign_id = serializers.CharField(required=False)
