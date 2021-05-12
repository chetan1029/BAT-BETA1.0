from django.db.models import Sum
from rest_framework import serializers

from bat.globalutils.utils import get_status_object
from bat.keywordtracking.constants import KEYWORD_STATUS_CHOICE
from bat.keywordtracking.models import Keyword, ProductKeyword, ProductKeywordRank
from bat.market.models import AmazonProduct
from bat.market.serializers import AmazonMarketplaceSerializer, AmazonProductSerializer
from bat.serializersFields.serializers_fields import StatusField


class KeywordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Keyword
        fields = ("id", "name", "frequency", "amazonmarketplace")
        read_only_fields = ("id",)


class ProductKeywordSerializer(serializers.ModelSerializer):
    keyword = KeywordSerializer()
    status = StatusField(choices=KEYWORD_STATUS_CHOICE)

    class Meta:
        model = ProductKeyword
        fields = ("id", "amazonproduct", "keyword", "status")
        read_only_fields = ("id",)


class ProductKeywordRankSerializer(serializers.ModelSerializer):
    productkeyword = ProductKeywordSerializer()

    class Meta:
        model = ProductKeywordRank
        fields = (
            "id",
            "productkeyword",
            "index",
            "rank",
            "page",
            "frequency",
            "visibility_score",
            "date",
            "scrap_status",
            "extra_data",
        )
        read_only_fields = ("id", "extra_data")


class KeywordTrackingProductSerializer(AmazonProductSerializer):
    keywords = serializers.SerializerMethodField()
    visibility_score = serializers.SerializerMethodField()

    class Meta(AmazonProductSerializer.Meta):
        model = AmazonProduct
        fields = AmazonProductSerializer.Meta.fields + (
            "keywords",
            "visibility_score",
        )

    def get_keywords(self, obj):
        return ProductKeyword.objects.filter(amazonproduct__id=obj.id).count()

    def get_visibility_score(self, obj):
        return ProductKeywordRank.objects.filter(
            productkeyword__amazonproduct__id=obj.id
        ).aggregate(Sum("visibility_score"))["visibility_score__sum"]
