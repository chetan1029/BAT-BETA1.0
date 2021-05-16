import operator
from datetime import date

from django.db import transaction
from django.db.utils import IntegrityError
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg2.openapi import Response as SwaggerResponse
from drf_yasg2.utils import swagger_auto_schema
from dry_rest_permissions.generics import DRYPermissions
from rest_framework import status, viewsets
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action

from bat.company.utils import get_member
from bat.keywordtracking import constants, serializers
from bat.keywordtracking.models import Keyword, ProductKeyword, ProductKeywordRank
from bat.market.models import AmazonProduct
from bat.setting.utils import get_status

# Create your views here.


class ProductKeywordViewSet(viewsets.ModelViewSet):
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
        responses={status.HTTP_200_OK: SwaggerResponse({"detail": "string"})}
    ),
)

class ProductKeywordRankViewSet(viewsets.ModelViewSet):
    """Operations on Product Keyword Rank."""

    serializer_class = serializers.ProductKeywordRankSerializer
    queryset = ProductKeywordRank.objects.all()
    permission_classes = (IsAuthenticated,)
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["date", "productkeyword__amazonproduct"]
    search_fields = [
        "productkeyword__keyword__name",
        "productkeyword__amazonproduct__asin",
    ]

    @action(detail=False, methods=["post"])
    def bulk_action(self, request, *args, **kwargs):
        """Set the update_status_bulk action."""
        serializer = serializers.KeywordsBulkActionSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            ids = serializer.validated_data.get("ids")
            bulk_action = serializer.validated_data.get("action").lower()
            member = get_member(
                company_id=self.kwargs.get("company_pk", None),
                user_id=self.request.user.id,
            )
            if bulk_action == "delete":
                try:
                    ids_cant_delete = ProductKeywordRank.objects.bulk_delete(ids)
                    content = {"detail": _("All selected Keywords are deleted.")}
                    return Response(
                        content, status=status.HTTP_200_OK
                    )
                except IntegrityError:
                    return Response(
                        {"detail": _("Can't delete Keywords")},
                        status=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    )



class KeywordTrackingProductViewsets(viewsets.ReadOnlyModelViewSet):
    queryset = AmazonProduct.objects.all()
    serializer_class = serializers.KeywordTrackingProductSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["productkeyword__amazonproduct_id"]


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
            print(amazon_product)
            print(keywords)
            if operator.contains(keywords, ","):
                keywords = keywords.split(",")
            else:
                keywords = keywords.split("\n")
            amazonmarketplace = amazon_product.amazonaccounts.marketplace
            for word in keywords:
                keyword, _keyword_c = Keyword.objects.get_or_create(
                    amazonmarketplace=amazonmarketplace, name=word
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
                        product_keyword_rank = ProductKeywordRank.objects.create(
                            productkeyword=product_keyword
                        )
                except IntegrityError:
                    pass
        return Response(
            {"detail": _("keywords are saved.")}, status=status.HTTP_200_OK
        )


class OverallDashboardAPIView(APIView):
    def get(self, request, company_pk=None, **kwargs):
        stats = {
            "data": {
                "05/01/2021": 10,
                "05/02/2021": 20,
                "05/03/2021": 50,
                "05/04/2021": 4,
                "05/05/2021": 34,
                "05/07/2021": 67,
                "05/08/2021": 11,
                "05/09/2021": 120,
                "05/10/2021": 4,
                "05/12/2021": 56,
                "05/13/2021": 68,
            }
        }

        return Response(stats, status=status.HTTP_200_OK)
