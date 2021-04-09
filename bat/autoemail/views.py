from datetime import datetime

import pytz
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg2.openapi import Response as SwaggerResponse
from drf_yasg2.utils import swagger_auto_schema
from dry_rest_permissions.generics import DRYPermissions
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from bat.autoemail import serializers
from bat.autoemail.constants import (
    ORDER_EMAIL_STATUS_QUEUED,
    ORDER_EMAIL_STATUS_SCHEDULED,
    ORDER_EMAIL_STATUS_SEND,
)
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
class EmailCampaignViewsets(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
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
        queryset = super().filter_queryset(queryset)
        return queryset.filter(company__id=company_id).order_by("id")

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
            for product in products:
                products_title_s += product.amazonproduct.title + ", "
            context = {
                "order_id": order.order_id,
                "Product_title_s": products_title_s,
                "Seller_name": campaign.get_company().name,
            }
            if campaign.include_invoice:
                file_data = {
                    "name": "order_invoice_" + str(order.order_id),
                    "file_context": {
                        "data": "I am order",
                        "order_id": str(order.order_id),
                        "purchase_date": str(order.purchase_date),
                        "total_amount": str(order.amount),
                        "order_items": products,
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
            }
            if campaign.include_invoice:
                file_data = {
                    "name": "order_invoice_" + context["order_id"],
                    "file_context": {
                        "data": "I am order",
                        "order_id": context["order_id"],
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


class EmailQueueViewsets(viewsets.ReadOnlyModelViewSet):
    queryset = EmailQueue.objects.all()
    serializer_class = serializers.EmailQueueSerializer
    permission_classes = (IsAuthenticated,)

    def filter_queryset(self, queryset):
        company_id = self.kwargs.get("company_pk", None)
        queryset = super().filter_queryset(queryset)
        return queryset.filter(emailcampaign__company__id=company_id).order_by(
            "-create_date"
        )


class DashboardAPIView(APIView):
    def get(self, request, company_pk=None, **kwargs):

        dt_format = "%m/%d/%Y"

        all_amazon_orders = AmazonOrder.objects.filter(
            amazonaccounts__company_id=company_pk
        )

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
            all_amazon_orders = all_amazon_orders.filter(
                purchase_date__gte=start_date
            )
            all_email_queue = all_email_queue.filter(
                amazonorder__purchase_date__gte=start_date
            )
        if end_date:
            all_amazon_orders = all_amazon_orders.filter(
                purchase_date__lte=end_date
            )
            all_email_queue = all_email_queue.filter(
                amazonorder__purchase_date__lte=end_date
            )

        marketplace = request.GET.get("marketplace", None)
        if marketplace:
            marketplace = get_object_or_404(AmazonMarketplace, pk=marketplace)
            all_amazon_orders = all_amazon_orders.filter(
                amazonaccounts__marketplace_id=marketplace.id
            )

            all_email_queue = all_email_queue.filter(
                emailcampaign__amazonmarketplace_id=marketplace.id
            )

        currency = request.GET.get("currency", None)
        if currency:
            currency = currency.upper()
            all_amazon_orders = all_amazon_orders.filter(
                amount_currency=currency
            )

            all_email_queue = all_email_queue.filter(
                amazonorder__amount_currency=currency
            )

        total_orders = all_amazon_orders.count()

        total_sales = all_amazon_orders.aggregate(Sum("amount")).get(
            "amount__sum"
        )

        total_email_sent = all_email_queue.filter(
            status__name=ORDER_EMAIL_STATUS_SEND
        ).count()

        total_email_in_queue = all_email_queue.filter(
            status__name__in=[
                ORDER_EMAIL_STATUS_SCHEDULED,
                ORDER_EMAIL_STATUS_QUEUED,
            ]
        ).count()

        amount_par_day = list(
            all_amazon_orders.values("purchase_date__date")
            .annotate(total_amount=Sum("amount"))
            .values_list("purchase_date__date", "total_amount")
            .order_by("purchase_date__date")
        )
        data = {}
        for date, total_amount in amount_par_day:
            data[date.strftime(dt_format)] = total_amount

        stats = {
            "data": data,
            "total_sales": total_sales,
            "total_orders": total_orders,
            "total_email_sent": total_email_sent,
            "total_email_in_queue": total_email_in_queue,
        }

        return Response(stats, status=status.HTTP_200_OK)
