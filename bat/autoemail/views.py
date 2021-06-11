import json
from datetime import datetime, timedelta
from decimal import Decimal

import pytz
from django.db import transaction
from django.db.models import Count, F
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from djmoney.money import Money
from drf_yasg2.openapi import Response as SwaggerResponse
from drf_yasg2.utils import swagger_auto_schema
from dry_rest_permissions.generics import DRYPermissions
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from bat.autoemail import serializers
from bat.autoemail.constants import (
    ORDER_EMAIL_STATUS_OPTOUT,
    ORDER_EMAIL_STATUS_QUEUED,
    ORDER_EMAIL_STATUS_SCHEDULED,
    ORDER_EMAIL_STATUS_SEND,
    EMAIL_CAMPAIGN_STATUS_ACTIVE,
)
from bat.autoemail.filters import EmailQueueFilter
from bat.autoemail.models import (
    EmailCampaign,
    EmailQueue,
    EmailTemplate,
    GlobalEmailTemplate,
)
from bat.autoemail.utils import send_email
from bat.company.utils import get_member
from bat.globalutils.utils import get_compare_percentage, pdf_file_from_html
from bat.market.models import AmazonCompany, AmazonMarketplace, AmazonOrder
from bat.autoemail.tasks import email_queue_create_for_new_campaign


class GlobalEmailTemplateViewsets(viewsets.ReadOnlyModelViewSet):
    queryset = GlobalEmailTemplate.objects.all()
    serializer_class = serializers.GlobalEmailTemplateSerializer
    permission_classes = (IsAuthenticated,)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["user"] = self.request.user
        return context


@method_decorator(
    name="test_email",
    decorator=swagger_auto_schema(
        operation_description="test email for campaign!",
        request_body=serializers.TestEmailSerializer(),
        responses={status.HTTP_200_OK: SwaggerResponse({"detail": "string"})},
    ),
)
class EmailCampaignViewsets(viewsets.ModelViewSet):
    queryset = EmailCampaign.objects.all()
    serializer_class = serializers.EmailCampaignSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["name", "amazonmarketplace"]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        company_id = self.kwargs.get("company_pk", None)
        context["company_id"] = company_id
        context["user"] = self.request.user
        return context

    def filter_queryset(self, queryset):
        company_id = self.kwargs.get("company_pk", None)
        marketplace = self.request.GET.get("marketplace", None)
        queryset = super().filter_queryset(queryset)
        if marketplace:
            queryset = queryset.filter(amazonmarketplace_id=marketplace)
        return queryset.filter(company__id=company_id).order_by("id")

    def perform_create(self, serializer):
        """Set the data for who is the owner or creater."""
        member = get_member(
            company_id=self.kwargs.get("company_pk", None),
            user_id=self.request.user.id,
        )
        instance = serializer.save(company=member.company)
        if instance.status.name == EMAIL_CAMPAIGN_STATUS_ACTIVE:
            transaction.on_commit(
                lambda: email_queue_create_for_new_campaign.delay(instance.id)
            )

    @action(detail=True, methods=["post"])
    def test_email(self, request, company_pk=None, pk=None):
        """
        test email for campaign!
        """

        def _generate_pdf_file(data):
            context = data.get("file_context")
            name = data.get("name")
            f = pdf_file_from_html(
                context,
                "autoemail/order_invoice.html",
                name,
                as_File_obj=False,
            )
            return f

        _member = get_member(
            company_id=company_pk, user_id=self.request.user.id
        )

        context = self.get_serializer_context()

        serializer = serializers.TestEmailSerializer(
            data=request.data, context=context
        )
        if not serializer.is_valid():
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        email = serializer.data["email"]
        campaign = self.get_object()

        order = AmazonOrder.objects.filter(
            amazonaccounts__marketplace_id=campaign.amazonmarketplace.id,
            amazonaccounts__company_id=company_pk,
        ).first()

        if order:
            products = order.orderitem_order.all()
            products_title_s = ""
            asins = ""
            skus = ""
            for product in products:
                products_title_s += product.amazonproduct.title + ", "
                asins += product.amazonproduct.asin + ","
                skus += product.amazonproduct.sku + ","

            marketplace_domain = (
                campaign.amazonmarketplace.sales_channel_name.lower()
            )
            # For the email description and title
            context = {
                "order_id": order.order_id,
                "product_title": products_title_s,
                "marketplace_domain": marketplace_domain,
                "seller_name": campaign.get_company().store_name,
                "purchase_date": str(order.purchase_date.strftime("%d %B %Y")),
                "payment_date": str(order.payment_date.strftime("%d %B %Y")),
                "shipment_date": str(order.shipment_date.strftime("%d %B %Y")),
                "delivery_date": str(
                    order.reporting_date.strftime("%d %B %Y")
                ),
                "order_items_count": str(order.quantity),
                "total_amount": str(order.amount),
                "order_items": products,
                "asin": asins,
                "sku": skus,
                "product_review_link": '<a href="https://www.'
                + marketplace_domain
                + "/review/review-your-purchases/ref=?_encoding=UTF8&amp;asins="
                + asins
                + '" target="_blank">Write your review here</a>',
                "feedback_review_link": '<a href="https://www.'
                + marketplace_domain
                + "/hz/feedback/?_encoding=UTF8&amp;orderID="
                + order.order_id
                + '" target="_blank">Leave feedback</a>',
            }

            if campaign.include_invoice:
                grand_total = order.amount + order.tax
                file_data = {
                    "name": "order_invoice_" + str(order.order_id),
                    "file_context": {
                        "sales_channel": str(order.sales_channel),
                        "order_id": str(order.order_id),
                        "purchase_date": str(
                            order.purchase_date.strftime("%d %B %Y")
                        ),
                        "total_amount": str(order.amount),
                        "tax": str(order.tax),
                        "order_items": products,
                        "company": campaign.get_company(),
                        "vat_tax_included": order.amazonaccounts.marketplace.vat_tax_included,
                        "grand_total": str(grand_total),
                    },
                }
                f = _generate_pdf_file(file_data)
                send_email(
                    campaign.emailtemplate,
                    email,
                    context=context,
                    attachment_files=[f],
                )
            else:
                send_email(campaign.emailtemplate, email, context=context)
        else:
            context = {
                "order_id": "#123",
                "Product_title_s": "XYZ Product",
                "Seller_name": campaign.get_company().name,
                "marketplace_domain": "amazon.com",
                "asin": "BRTFDDG0",
            }
            if campaign.include_invoice:
                file_data = {
                    "name": "order_invoice_" + context["order_id"],
                    "file_context": {
                        "seles_channel": str(order.sales_channel),
                        "order_id": context["order_id"],
                        "purchase_date": str(
                            datetime.now().strftime("%d %B %Y")
                        ),
                        "total_amount": str(25),
                        "tax": str(5),
                        "seller_name": campaign.get_company(),
                        "vat_tax_included": True,
                        "grand_total": str(25),
                        "vat_number": "SE123466770",
                    },
                }
                f = _generate_pdf_file(file_data)
                send_email(
                    campaign.emailtemplate,
                    email,
                    context=context,
                    attachment_files=[f],
                )
            else:
                send_email(campaign.emailtemplate, email, context=context)

        return Response(
            {"detail": _("email sent successfully")}, status=status.HTTP_200_OK
        )


class EmailTemplateViewsets(viewsets.ModelViewSet):
    queryset = EmailTemplate.objects.all()
    serializer_class = serializers.EmailTemplateSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ["name"]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        company_id = self.kwargs.get("company_pk", None)
        context["company_id"] = company_id
        context["user"] = self.request.user
        return context

    def filter_queryset(self, queryset):
        company_id = self.kwargs.get("company_pk", None)
        queryset = super().filter_queryset(queryset)
        return queryset.filter(company__id=company_id).order_by("id")

    def perform_create(self, serializer):
        """Set the data for who is the owner or creater."""
        member = get_member(
            company_id=self.kwargs.get("company_pk", None),
            user_id=self.request.user.id,
        )
        serializer.save(company=member.company)

    @action(detail=True, methods=["post"])
    def test_email(self, request, company_pk=None, pk=None):
        """
        test email for template!
        """

        def _generate_pdf_file(data):
            context = data.get("file_context")
            name = data.get("name")
            f = pdf_file_from_html(
                context,
                "autoemail/order_invoice.html",
                name,
                as_File_obj=False,
            )
            return f

        member = get_member(
            company_id=company_pk, user_id=self.request.user.id
        )
        company = member.company

        context = self.get_serializer_context()

        serializer = serializers.TestEmailSerializer(
            data=request.data, context=context
        )
        if not serializer.is_valid():
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        email = serializer.data["email"]
        campaign_id = serializer.data.get("campaign_id", None)
        template = self.get_object()

        campaign = ""
        if campaign_id:
            campaign = EmailCampaign.objects.get(
                pk=campaign_id, company=company
            )

        if campaign:
            order = AmazonOrder.objects.filter(
                amazonaccounts__marketplace_id=campaign.amazonmarketplace.id,
                amazonaccounts__company_id=company_pk,
            )
        else:
            order = AmazonOrder.objects.filter(
                amazonaccounts__company_id=company_pk
            )
        if order.exists():
            order = order.first()
            products = order.orderitem_order.all()
            products_title = list(
                products.values_list("amazonproduct__title", flat=True)
            )
            products_asin = list(
                products.values_list("amazonproduct__asin", flat=True)
            )
            products_sku = list(
                products.values_list("amazonproduct__sku", flat=True)
            )
            products_title_s = ",".join(products_title)
            asins = ",".join(products_asin)
            skus = ",".join(products_sku)

            marketplace_domain = (
                order.amazonaccounts.marketplace.sales_channel_name.lower()
            )

            order_id = order.order_id
            purchase_date = order.purchase_date.strftime("%d %B %Y")
            payment_date = order.payment_date.strftime("%d %B %Y")
            shipment_date = order.shipment_date.strftime("%d %B %Y")
            delivery_date = order.reporting_date.strftime("%d %B %Y")
            order_items_count = order.quantity
            total_amount = order.amount
            if order.tax:
                taxes = order.tax
                grand_total = order.amount + order.tax
            else:
                taxes = 0
                grand_total = order.amount
            vat_tax_included = (
                order.amazonaccounts.marketplace.vat_tax_included
            )

            if campaign:
                company_detail = campaign.get_company()
                vat_number = company_detail.vat_number
            else:
                company_detail = AmazonCompany.objects.get(
                    amazonaccounts=order.amazonaccounts
                )
                vat_number = ""

            store_name = company_detail.store_name

        else:
            order_id = "1234567890"
            products_title_s = "Product XYZ"
            asins = "XYS345"
            skus = "XYZ_PRODUCT_SKU"
            marketplace_domain = "amazon.com"
            purchase_date = datetime.now().strftime("%d %B %Y")
            payment_date = datetime.now().strftime("%d %B %Y")
            shipment_date = datetime.now().strftime("%d %B %Y")
            delivery_date = datetime.now().strftime("%d %B %Y")
            order_items_count = 2
            total_amount = 200
            taxes = 20
            grand_total = total_amount + taxes
            store_name = "STORE XYZ"
            vat_tax_included = True
            vat_number = "SE123456789"

        context = {
            "order_id": order_id,
            "product_title": products_title_s,
            "marketplace_domain": marketplace_domain,
            "seller_name": store_name,
            "purchase_date": str(purchase_date),
            "payment_date": str(payment_date),
            "shipment_date": str(shipment_date),
            "delivery_date": str(delivery_date),
            "order_items_count": str(order_items_count),
            "total_amount": str(total_amount),
            "order_items": products,
            "asin": asins,
            "sku": skus,
            "product_review_link": '<a href="https://www.'
            + marketplace_domain
            + "/review/review-your-purchases/ref=?_encoding=UTF8&amp;asins="
            + asins
            + '" target="_blank">Write your review here</a>',
            "feedback_review_link": '<a href="https://www.'
            + marketplace_domain
            + "/hz/feedback/?_encoding=UTF8&amp;orderID="
            + order_id
            + '" target="_blank">Leave feedback</a>',
        }

        if campaign and campaign.include_invoice:
            file_data = {
                "name": "order_invoice_" + str(order_id),
                "file_context": {
                    "sales_channel": str(marketplace_domain),
                    "order_id": str(order_id),
                    "purchase_date": str(purchase_date),
                    "total_amount": str(total_amount),
                    "tax": str(taxes),
                    "order_items": products,
                    "company": campaign.get_company(),
                    "vat_tax_included": vat_tax_included,
                    "grand_total": str(grand_total),
                    "vat_number": str(vat_number),
                },
            }
            f = _generate_pdf_file(file_data)
            send_email(
                campaign.emailtemplate,
                email,
                context=context,
                attachment_files=[f],
            )
        else:
            send_email(template, email, context=context)

        return Response(
            {"detail": _("email sent successfully")}, status=status.HTTP_200_OK
        )


class EmailQueueViewsets(viewsets.ReadOnlyModelViewSet):
    queryset = EmailQueue.objects.all()
    serializer_class = serializers.EmailQueueSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = EmailQueueFilter
    search_fields = ["=amazonorder__order_id"]

    def filter_queryset(self, queryset):
        company_id = self.kwargs.get("company_pk", None)
        queryset = super().filter_queryset(queryset)
        return queryset.filter(
            emailcampaign__company__id=company_id,
            amazonorder__purchase_date__gte=F(
                "emailcampaign__activation_date"
            ),
        ).order_by("-create_date")


class EmailChartDataAPIView(APIView):
    def get(self, request, company_pk=None, **kwargs):

        dt_format = "%m/%d/%Y"

        all_email_queue = EmailQueue.objects.filter(
            emailcampaign__company_id=company_pk
        )

        marketplace = request.GET.get("marketplace", None)
        if marketplace and marketplace != "all":
            marketplace = get_object_or_404(AmazonMarketplace, pk=marketplace)
            all_email_queue = all_email_queue.filter(
                emailcampaign__amazonmarketplace_id=marketplace.id
            )

        start_date = self.request.GET.get("start_date")
        end_date = self.request.GET.get("end_date")

        start_date = (
            pytz.utc.localize(datetime.strptime(start_date, dt_format))
            if start_date
            else None
        )
        end_date = (
            pytz.utc.localize(datetime.strptime(end_date, dt_format))
            if end_date
            else None
        )

        difference_days = 0
        if start_date and end_date:
            days = end_date - start_date
            difference_days = days.days
        start_date_compare = start_date - timedelta(days=difference_days)
        end_date_compare = end_date - timedelta(days=difference_days)

        all_email_queue_compare = all_email_queue

        if start_date:
            all_email_queue = all_email_queue.filter(
                schedule_date__gte=start_date
            )
            all_email_queue_compare = all_email_queue_compare.filter(
                schedule_date__gte=start_date_compare
            )
        if end_date:
            all_email_queue = all_email_queue.filter(
                schedule_date__lte=end_date
            )
            all_email_queue_compare = all_email_queue_compare.filter(
                schedule_date__lte=end_date_compare
            )

        email_par_day = list(
            all_email_queue.filter(status__name=ORDER_EMAIL_STATUS_SEND)
            .values("send_date__date")
            .annotate(total_email=Count("id"))
            .values_list("send_date__date", "total_email")
            .order_by("send_date__date")
        )
        data = {}
        try:
            for date, total_email in email_par_day:
                data[date.strftime(dt_format)] = total_email
        except AttributeError:
            print("Date might be null and stftime can't be apply on it.")

        # original stats
        total_email_sent = all_email_queue.filter(
            status__name=ORDER_EMAIL_STATUS_SEND
        ).count()

        total_opt_out_email = all_email_queue.filter(
            status__name=ORDER_EMAIL_STATUS_OPTOUT
        ).count()

        opt_out_rate = 0
        if total_opt_out_email and total_email_sent:
            opt_out_rate = round(
                (total_opt_out_email / total_email_sent) * 100, 2
            )

        total_email_in_queue = all_email_queue.filter(
            status__name__in=[
                ORDER_EMAIL_STATUS_SCHEDULED,
                ORDER_EMAIL_STATUS_QUEUED,
            ],
            amazonorder__purchase_date__gte=F(
                "emailcampaign__activation_date"
            ),
        ).count()

        # Compare email stats.
        total_email_sent_compare = all_email_queue_compare.filter(
            status__name=ORDER_EMAIL_STATUS_SEND
        ).count()

        total_opt_out_email_compare = all_email_queue_compare.filter(
            status__name=ORDER_EMAIL_STATUS_OPTOUT
        ).count()

        opt_out_rate_compare = 0
        if total_opt_out_email_compare and total_email_sent_compare:
            opt_out_rate_compare = round(
                (total_opt_out_email_compare / total_email_sent_compare) * 100,
                2,
            )

        total_email_in_queue_compare = all_email_queue_compare.filter(
            status__name__in=[
                ORDER_EMAIL_STATUS_SCHEDULED,
                ORDER_EMAIL_STATUS_QUEUED,
            ],
            amazonorder__purchase_date__gte=F(
                "emailcampaign__activation_date"
            ),
        ).count()

        # Comapre percentage
        total_email_sent_percentage = get_compare_percentage(
            total_email_sent, total_email_sent_compare
        )
        total_opt_out_email_percentage = get_compare_percentage(
            total_opt_out_email, total_opt_out_email_compare
        )
        opt_out_rate_percentage = get_compare_percentage(
            opt_out_rate, opt_out_rate_compare
        )
        total_email_in_queue_percentage = get_compare_percentage(
            total_email_in_queue, total_email_in_queue_compare
        )

        stats = {
            "chartData": [{"name": "Email Sent", "data": data}],
            "stats": {
                "total_email_sent": total_email_sent,
                "total_email_in_queue": total_email_in_queue,
                "total_opt_out_email": total_opt_out_email,
                "opt_out_rate": opt_out_rate,
                "email_sent_percentage": total_email_sent_percentage,
                "opt_out_email_percentage": total_opt_out_email_percentage,
                "opt_out_rate_percentage": opt_out_rate_percentage,
                "email_in_queue_percentage": total_email_in_queue_percentage,
            },
        }

        return Response(stats, status=status.HTTP_200_OK)
