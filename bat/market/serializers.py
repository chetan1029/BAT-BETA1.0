from rest_framework import serializers

from bat.market.models import AmazonMarketplace

from bat.serializersFields.serializers_fields import CountrySerializerField


class AmazonMarketplaceSerializer(serializers.ModelSerializer):
    country = CountrySerializerField(required=False)

    class Meta:
        model = AmazonMarketplace
        fields = ("name", "country", "marketplaceId", "region",)
