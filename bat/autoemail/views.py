import json
from datetime import datetime
from decimal import Decimal

import pytz
from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
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
)
from bat.autoemail.filters import EmailQueueFilter
from bat.autoemail.models import EmailCampaign, EmailQueue, EmailTemplate
from bat.autoemail.utils import send_email
from bat.company.utils import get_member
from bat.globalutils.utils import pdf_file_from_html
from bat.market.models import AmazonMarketplace, AmazonOrder, AmazonOrderItem


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
        serializer.save(company=member.company)

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
            for product in products:
                products_title_s += product.amazonproduct.title + ", "
                asins += product.amazonproduct.asin + ","
            # For the email description and title
            context = {
                "order_id": order.order_id,
                "Product_title_s": products_title_s,
                "marketplace_domain": campaign.amazonmarketplace.sales_channel_name.lower(),
                "Seller_name": campaign.get_company().store_name,
                "asin": asins,
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
        return queryset.filter(emailcampaign__company__id=company_id).order_by(
            "-create_date"
        )


class EmailChartDataAPIView(APIView):
    def get(self, request, company_pk=None, **kwargs):

        dt_format = "%m/%d/%Y"

        all_email_queue = EmailQueue.objects.filter(
            emailcampaign__company_id=company_pk
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

        if start_date:
            all_email_queue = all_email_queue.filter(send_date__gte=start_date)
        if end_date:
            all_email_queue = all_email_queue.filter(send_date__lte=end_date)

        marketplace = request.GET.get("marketplace", None)
        if marketplace and marketplace != "all":
            marketplace = get_object_or_404(AmazonMarketplace, pk=marketplace)
            all_email_queue = all_email_queue.filter(
                emailcampaign__amazonmarketplace_id=marketplace.id
            )

        email_par_day = list(
            all_email_queue.values("send_date__date")
            .annotate(total_email=Count("id"))
            .values_list("send_date__date", "total_email")
            .order_by("send_date__date")
        )
        data = {}
        for date, total_amount in email_par_day:
            data[date.strftime(dt_format)] = total_amount

        total_email_sent = all_email_queue.filter(
            status__name=ORDER_EMAIL_STATUS_SEND
        ).count()

        total_opt_out_email = all_email_queue.filter(
            status__name=ORDER_EMAIL_STATUS_OPTOUT
        ).count()

        opt_out_rate = 0
        if total_opt_out_email:
            opt_out_rate = round((total_email_sent / total_opt_out_email), 2)

        total_email_in_queue = all_email_queue.filter(
            status__name__in=[
                ORDER_EMAIL_STATUS_SCHEDULED,
                ORDER_EMAIL_STATUS_QUEUED,
            ]
        ).count()

        stats = {
            "chartData": [{"name": "Email Sent", "data": data}],
            "stats": {
                "total_email_sent": total_email_sent,
                "total_email_in_queue": total_email_in_queue,
                "total_opt_out_email": total_opt_out_email,
                "opt_out_rate": opt_out_rate,
            },
        }

        return Response(stats, status=status.HTTP_200_OK)
