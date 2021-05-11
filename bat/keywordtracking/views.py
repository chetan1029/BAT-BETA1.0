from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
from dry_rest_permissions.generics import DRYPermissions
from rest_framework import viewsets
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated

from bat.keywordtracking import serializers
from bat.keywordtracking.models import Keyword, ProductKeyword, ProductKeywordRank

# Create your views here.


class KeywordViewSet(viewsets.ModelViewSet):
    """Operations on Keywords."""

    serializer_class = serializers.KeywordSerializer
    queryset = Keyword.objects.all()
    permission_classes = (IsAuthenticated, DRYPermissions)
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["is_active", "payment_days"]
    search_fields = ["title"]
