import json
import operator
from datetime import datetime, timedelta

import pytz
from django.conf import settings
from django.db import transaction
from django.db.models import F, Q, Sum
from django.db.models.aggregates import Avg
from django.db.utils import IntegrityError
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django_auto_prefetching import AutoPrefetchViewSetMixin
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg2.openapi import Response as SwaggerResponse
from drf_yasg2.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from bat.company.utils import get_member
from bat.keywordtracking import constants, serializers
from bat.keywordtracking.models import (
    GlobalKeyword,
    Keyword,
    ProductKeyword,
    ProductKeywordRank,
)
from bat.keywordtracking.utils import get_compare_percentage
from bat.market.amazon_ad_api import Keywords
from bat.market.models import (
    AmazonAccounts,
    AmazonMarketplace,
    AmazonOrder,
    AmazonProduct,
    AmazonProductSessions,
    PPCCredentials,
    PPCProfile,
)
from bat.setting.utils import get_status

# Create your views here.


class ProductKeywordViewSet(AutoPrefetchViewSetMixin, viewsets.ModelViewSet):
    """Operations on Product Keywords."""

    serializer_class = serializers.ProductKeywordSerializer
    queryset = ProductKeyword.objects.all()
    permission_classes = (IsAuthenticated,)
    filter_backends = [DjangoFilterBackend, SearchFilter]
    # filterset_fields = ["name", "amazonmarketplace"]
    search_fields = ["keyword__name", "amazonproduct__asin"]


@method_decorator(
    name="bulk_action",
    decorator=swagger_auto_schema(
        operation_description="Performs the given action on provided set of Keyword ids. Available actions are: delete.",
        request_body=serializers.KeywordsBulkActionSerializer(),
        responses={status.HTTP_200_OK: SwaggerResponse({"detail": "string"})},
    ),
)
class ProductKeywordRankViewSet(
    AutoPrefetchViewSetMixin, viewsets.ModelViewSet
):
    """Operations on Product Keyword Rank."""

    serializer_class = serializers.ProductKeywordRankSerializer
    queryset = ProductKeywordRank.objects.all()
    permission_classes = (IsAuthenticated,)
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["date", "productkeyword__amazonproduct"]
    search_fields = [
        "productkeyword__keyword__name",
        "productkeyword__amazonproduct__asin",
    ]
    ordering_fields = [
        "frequency",
        "rank",
        "id",
        "index",
        "visibility_score",
        "productkeyword__keyword__name",
    ]

    def filter_queryset(self, queryset):
        company_id = self.kwargs.get("company_pk", None)
        _member = get_member(
            company_id=company_id, user_id=self.request.user.id
        )
        queryset = super().filter_queryset(queryset)
        return queryset.filter(company_id=company_id).order_by("-date")

    @action(detail=False, methods=["post"])
    def bulk_action(self, request, *args, **kwargs):
        """Set the update_status_bulk action."""
        serializer = serializers.KeywordsBulkActionSerializer(
            data=request.data
        )
        if serializer.is_valid(raise_exception=True):
            ids = serializer.validated_data.get("ids")
            bulk_action = serializer.validated_data.get("action").lower()
            member = get_member(
                company_id=self.kwargs.get("company_pk", None),
                user_id=self.request.user.id,
            )
            if bulk_action == "delete":
                try:
                    ids_cant_delete = ProductKeywordRank.objects.bulk_delete(
                        ids
                    )
                    content = {
                        "detail": _("All selected Keywords are deleted.")
                    }
                    return Response(content, status=status.HTTP_200_OK)
                except IntegrityError:
                    return Response(
                        {"detail": _("Can't delete Keywords")},
                        status=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    )


class KeywordTrackingProductViewsets(
    AutoPrefetchViewSetMixin, viewsets.ReadOnlyModelViewSet
):
    queryset = AmazonProduct.objects.all()
    serializer_class = serializers.KeywordTrackingProductSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["status__name"]

    def filter_queryset(self, queryset):
        company_id = self.kwargs.get("company_pk", None)
        _member = get_member(
            company_id=company_id, user_id=self.request.user.id
        )
        queryset = super().filter_queryset(queryset)
        return queryset.filter(amazonaccounts__company_id=company_id).order_by(
            "-create_date"
        )


@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        operation_description="Save keywords for given product.",
        request_body=serializers.SaveKeywordSerializer(),
        responses={status.HTTP_200_OK: SwaggerResponse({"detail": "string"})},
    ),
)
class SaveProductKeyword(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, company_pk=None, **kwargs):
        member = get_member(company_id=company_pk, user_id=request.user.id)
        serializer = serializers.SaveKeywordSerializer(
            data=request.data, context={"member": member}
        )
        if serializer.is_valid(raise_exception=True):
            amazon_product = AmazonProduct.objects.get(
                pk=serializer.validated_data.get("amazon_product_pk")
            )
            keywords = serializer.validated_data.get("keywords")

            if operator.contains(keywords, ","):
                keywords = keywords.split(",")
            else:
                keywords = keywords.split("\n")
            amazonmarketplace = amazon_product.amazonaccounts.marketplace
            for word in keywords:

                search_frequency = 0
                globalkeyword = GlobalKeyword.objects.filter(
                    department=amazonmarketplace.sales_channel_name, name=word
                )
                if globalkeyword.exists():
                    search_frequency = globalkeyword.first().frequency

                keyword, _keyword_c = Keyword.objects.update_or_create(
                    amazonmarketplace=amazonmarketplace,
                    name=word,
                    defaults={"frequency": search_frequency},
                )

                product_keyword, _product_keyword_C = ProductKeyword.objects.get_or_create(
                    amazonproduct=amazon_product,
                    keyword=keyword,
                    defaults={
                        "status": get_status(
                            constants.KEYWORD_PARENT_STATUS,
                            constants.KEYWORD_STATUS_ACTIVE,
                        )
                    },
                )
                try:
                    with transaction.atomic():
                        ProductKeywordRank.objects.create(
                            company_id=company_pk,
                            productkeyword=product_keyword,
                            frequency=search_frequency,
                        )
                except IntegrityError:
                    pass
        return Response(
            {"detail": _("keywords are saved.")}, status=status.HTTP_200_OK
        )


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="dashboard data for product keyword rank.",
        responses={
            status.HTTP_200_OK: SwaggerResponse(
                [{"name": "string", "data": "list"}]
            )
        },
    ),
)
class OverallDashboardAPIView(APIView):
    def get(self, request, company_pk=None, **kwargs):

        _member = get_member(company_id=company_pk, user_id=request.user.id)

        all_product_keyword_rank = ProductKeywordRank.objects.filter(
            company_id=company_pk
        ).order_by("-date")

        dt_format = "%m/%d/%Y"

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
            all_product_keyword_rank = all_product_keyword_rank.filter(
                date__gte=start_date
            )
        if end_date:
            all_product_keyword_rank = all_product_keyword_rank.filter(
                date__lte=end_date
            )

        marketplace = request.GET.get("marketplace", None)
        if marketplace:
            try:
                marketplace = get_object_or_404(
                    AmazonMarketplace, pk=marketplace
                )
                all_product_keyword_rank = all_product_keyword_rank.filter(
                    productkeyword__amazonproduct__amazonaccounts__marketplace_id=marketplace.id
                )
            except ValueError as e:
                return Response(
                    {"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST
                )

        product_keyword_rank_par_day = list(
            all_product_keyword_rank.values("date")
            .annotate(sum_visibility_score=Sum("visibility_score"))
            .values_list("date", "sum_visibility_score")
            .order_by("date")
        )

        data = {}
        for date, sum_visibility_score in product_keyword_rank_par_day:
            data[date.strftime(dt_format)] = int(sum_visibility_score)

        stats = [{"name": "Visibilty Score", "data": data}]

        return Response(stats, status=status.HTTP_200_OK)


class ProductKeywordAPIView(APIView):
    def get(self, request, company_pk=None, product_keyword_pk=None, **kwargs):

        _member = get_member(company_id=company_pk, user_id=request.user.id)

        _product_keyword = get_object_or_404(
            ProductKeyword,
            pk=product_keyword_pk,
            amazonproduct__amazonaccounts__company_id=company_pk,
        )

        all_product_keyword_rank = ProductKeywordRank.objects.filter(
            productkeyword_id=product_keyword_pk
        ).order_by("-date")

        dt_format = "%m/%d/%Y"

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
            all_product_keyword_rank = all_product_keyword_rank.filter(
                date__gte=start_date
            )
        if end_date:
            all_product_keyword_rank = all_product_keyword_rank.filter(
                date__lte=end_date
            )

        all_product_keyword_rank = all_product_keyword_rank.values_list(
            "date", "visibility_score", "rank"
        )

        visibility_score_data = {}
        rank_data = {}

        for date, visibility_score, rank in all_product_keyword_rank:
            visibility_score_data[date.strftime(dt_format)] = visibility_score
            rank_data[date.strftime(dt_format)] = rank

        stats = [
            {"name": "Visibilty Score", "data": visibility_score_data},
            {"name": "Rank", "data": rank_data},
        ]
        return Response(stats, status=status.HTTP_200_OK)


class SuggestKeywordAPIView(APIView):
    def get(self, request, company_pk=None, **kwargs):

        _member = get_member(company_id=company_pk, user_id=request.user.id)

        amazonaccount_id = self.request.GET.get("amazonaccount_id")
        amazonaccount = get_object_or_404(AmazonAccounts, pk=amazonaccount_id)
        ad_region = settings.SELLING_REGIONS.get(
            amazonaccount.marketplace.region
        ).get("ad_region")

        asins = self.request.GET.get("asins")
        asins = asins.split(",")

        credentials = PPCCredentials.objects.first()
        ppcprofile = PPCProfile.objects.filter(
            amazonmarketplace=amazonaccount.marketplace
        ).first()
        keyword_list = []
        if ppcprofile:
            if credentials:
                KeywordsAPI = Keywords(
                    credentials.access_token,
                    credentials.refresh_token,
                    scope=ppcprofile.profile_id,
                    region=ad_region,
                )
                KeywordsAPI.do_refresh_token()
                params = {"maxNumSuggestions": 1000}

                for asin in asins:
                    keywords = KeywordsAPI.get_asin_suggested_keywords(
                        asin, params
                    )
                    for keyword in keywords:
                        keyword_list.append(keyword["keywordText"])

        suggested_keywords = (
            GlobalKeyword.objects.filter(
                Q(asin_1__in=asins) | Q(asin_2__in=asins) | Q(asin_3__in=asins)
            )
            .filter(department=amazonaccount.marketplace.sales_channel_name)
            .order_by("-frequency")
        )

        suggested_keywords = (
            list(suggested_keywords.values_list("name", flat=True))
            + keyword_list
        )

        stats = {"data": suggested_keywords}
        return Response(stats, status=status.HTTP_200_OK)


class AsinPerformanceView(APIView):
    def get(self, request, company_pk=None, product_keyword_pk=None, **kwargs):

        _member = get_member(company_id=company_pk, user_id=request.user.id)

        product_visibility = ProductKeywordRank.objects.filter(
            company_id=company_pk
        )

        marketplace = request.GET.get("marketplace", None)
        if marketplace and marketplace != "all":
            try:
                marketplace = get_object_or_404(
                    AmazonMarketplace, pk=marketplace
                )
                product_visibility = product_visibility.filter(
                    productkeyword__amazonproduct__amazonaccounts__marketplace_id=marketplace.id
                )
            except ValueError as e:
                return Response(
                    {"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST
                )

        dt_format = "%m/%d/%Y"
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
            product_visibility = product_visibility.filter(
                date__gte=start_date
            )
        if end_date:
            product_visibility = product_visibility.filter(date__lte=end_date)

        product_visibility = product_visibility.values(
            asin=F("productkeyword__amazonproduct__asin")
        ).annotate(sum_visibility_score=Sum("visibility_score"))

        best = product_visibility.order_by("-sum_visibility_score", "asin")[
            :10
        ]
        worst = product_visibility.order_by("sum_visibility_score", "asin")[
            :10
        ]
        trending = product_visibility.order_by(
            "-sum_visibility_score", "asin"
        )[:10]

        stats = [{"best": best, "worst": worst, "trending": trending}]
        return Response(stats, status=status.HTTP_200_OK)


class SalesChartDataAPIView(APIView):
    def get(self, request, company_pk=None, **kwargs):

        dt_format = "%m/%d/%Y"

        all_amazon_orders = AmazonOrder.objects.filter(
            amazonaccounts__company_id=company_pk
        )

        all_amazon_conversion = AmazonProductSessions.objects.filter(
            amazonproduct__amazonaccounts__company_id=company_pk
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

        marketplace = request.GET.get("marketplace", None)
        if marketplace and marketplace != "all":
            marketplace = get_object_or_404(AmazonMarketplace, pk=marketplace)
            all_amazon_orders = all_amazon_orders.filter(
                amazonaccounts__marketplace_id=marketplace.id
            )
            all_amazon_conversion = all_amazon_conversion.filter(
                amazonproduct__amazonaccounts__marketplace_id=marketplace.id
            )

        currency = request.GET.get("currency", None)
        if currency:
            currency = currency.upper()
            all_amazon_orders = all_amazon_orders.filter(
                amount_currency=currency
            )

        difference_days = 0
        if start_date and end_date:
            days = end_date - start_date
            difference_days = days.days
        start_date_compare = start_date - timedelta(days=difference_days)
        end_date_compare = end_date - timedelta(days=difference_days)

        all_amazon_orders_compare = all_amazon_orders

        if start_date:
            all_amazon_orders = all_amazon_orders.filter(
                purchase_date__gte=start_date
            )
            all_amazon_conversion = all_amazon_conversion.filter(
                date__gte=start_date
            )

            # Campare data for same date difference
            all_amazon_orders_compare = all_amazon_orders_compare.filter(
                purchase_date__gte=start_date_compare
            )

        if end_date:
            all_amazon_orders = all_amazon_orders.filter(
                purchase_date__lte=end_date
            )
            all_amazon_conversion = all_amazon_conversion.filter(
                date__lte=end_date
            )

            # Campare data for same date difference
            all_amazon_orders_compare = all_amazon_orders_compare.filter(
                purchase_date__lte=end_date_compare
            )

        total_orders = all_amazon_orders.count()

        total_sales = all_amazon_orders.aggregate(Sum("amount")).get(
            "amount__sum"
        )

        total_orders_compare = all_amazon_orders_compare.count()

        total_sales_compare = all_amazon_orders_compare.aggregate(
            Sum("amount")
        ).get("amount__sum")

        print(str(total_sales) + " " + str(total_sales_compare))
        print(str(total_orders) + " " + str(total_orders_compare))

        total_orders_percentage = get_compare_percentage(
            total_orders, total_orders_compare
        )
        total_sales_percentage = get_compare_percentage(
            total_sales, total_sales_compare
        )

        amount_par_day = list(
            all_amazon_orders.values("purchase_date__date")
            .annotate(total_amount=Sum("amount"))
            .values_list("purchase_date__date", "total_amount")
            .order_by("purchase_date__date")
        )

        conversion_per_day = list(
            all_amazon_conversion.values("date")
            .annotate(avg_conversion_rate=Avg("conversion_rate"))
            .values_list("date", "avg_conversion_rate")
            .order_by("date")
        )

        conversion_data = {}
        for date, avg_conversion_rate in conversion_per_day:
            conversion_data[date.strftime(dt_format)] = avg_conversion_rate

        amount_data = {}
        for date, total_amount in amount_par_day:
            amount_data[date.strftime(dt_format)] = total_amount

        stats = {
            "chartData": [
                {"name": "Amount", "data": amount_data},
                {"name": "Conversion Rate", "data": conversion_data},
            ],
            "stats": {
                "total_sales": total_sales,
                "total_orders": total_orders,
                "total_sales_percentage": total_sales_percentage,
                "total_orders_percentage": total_orders_percentage,
            },
        }

        return Response(stats, status=status.HTTP_200_OK)
