from bat.autoemail.serializers import (
    AmazonMarketplaceSerializer,
    AmazonProductSerializer,
)
from bat.globalutils.utils import get_status_object
from bat.keywordtracking.constants import KEYWORD_STATUS_CHOICE
from bat.keywordtracking.models import Keyword, ProductKeyword, ProductKeywordRank
from bat.serializersFields.serializers_fields import StatusField


class KeywordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Keyword
        fields = ("id", "name", "frequency")
        read_only_fields = ("id",)


class ProductKeywordSerializer(serializers.ModelSerializer):
    amazonproduct = AmazonProductSerializer(read_only=True)
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
