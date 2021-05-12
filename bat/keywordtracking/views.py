from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
from dry_rest_permissions.generics import DRYPermissions
from rest_framework import viewsets
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated

from bat.keywordtracking import serializers
from bat.keywordtracking.models import Keyword, ProductKeyword, ProductKeywordRank
from bat.market.models import AmazonProduct

# Create your views here.


class ProductKeywordViewSet(viewsets.ModelViewSet):
    """Operations on Product Keywords."""

    serializer_class = serializers.ProductKeywordSerializer
    queryset = ProductKeyword.objects.all()
    permission_classes = (IsAuthenticated,)
    filter_backends = [DjangoFilterBackend, SearchFilter]
    # filterset_fields = ["name", "amazonmarketplace"]
    search_fields = ["keyword__name", "amazonproduct__asin"]


class ProductKeywordRankViewSet(viewsets.ModelViewSet):
    """Operations on Product Keyword Rank."""

    serializer_class = serializers.ProductKeywordRankSerializer
    queryset = ProductKeywordRank.objects.all()
    permission_classes = (IsAuthenticated,)
    filter_backends = [DjangoFilterBackend, SearchFilter]
    # filterset_fields = ["name", "amazonmarketplace"]
    search_fields = [
        "productkeyword__keyword__name",
        "productkeyword__amazonproduct__asin",
    ]


class KeywordTrackingProductViewsets(viewsets.ReadOnlyModelViewSet):
    queryset = AmazonProduct.objects.all()
    serializer_class = serializers.KeywordTrackingProductSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["name", "productkeyword__amazonproduct_id"]
