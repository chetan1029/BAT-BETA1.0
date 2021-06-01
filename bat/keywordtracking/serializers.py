from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Sum
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers

from bat.globalutils.utils import get_status_object
from bat.keywordtracking.constants import KEYWORD_STATUS_CHOICE
from bat.keywordtracking.models import Keyword, ProductKeyword, ProductKeywordRank
from bat.market.models import AmazonProduct
from bat.market.serializers import AmazonMarketplaceSerializer, AmazonProductSerializer
from bat.serializersFields.serializers_fields import StatusField


class KeywordSerializer(serializers.ModelSerializer):
    amazonmarketplace = AmazonMarketplaceSerializer(read_only=True)

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
        read_only_fields = fields


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
            productkeyword__amazonproduct__id=obj.id, date=timezone.now()
        ).aggregate(Sum("visibility_score"))["visibility_score__sum"]


class SaveKeywordSerializer(serializers.Serializer):
    amazon_product_pk = serializers.IntegerField(required=True)
    keywords = serializers.CharField(required=True)

    def validate(self, attrs):
        member = self.context.get("member")
        try:
            AmazonProduct.objects.get(
                pk=attrs.get("amazon_product_pk"),
                amazonaccounts__company_id=member.company.id,
                amazonaccounts__user_id=member.user.id,
            )
        except ObjectDoesNotExist:
            raise serializers.ValidationError(
                {"amazon_product_pk": _("Invalid product selectd.")}
            )
        return super().validate(attrs)


class KeywordsBulkActionSerializer(serializers.Serializer):
    ids = serializers.ListField(required=True)
    action = serializers.ChoiceField(
        required=True, choices=list(["delete", "Delete"])
    )

    def validate(self, attrs):
        data = super().validate(attrs)
        ids = list(filter(None, data.get("ids")))
        if not ids:
            raise ValidationError({"ids": "Id list should not empty."})
        data = data.copy()
        data["ids"] = ids
        return data
