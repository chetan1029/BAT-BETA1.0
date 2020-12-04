from rest_framework import serializers

from django_countries import countries

from bat.globalconstants.constants import CURRENCY_CODE_CHOICES


class XlsxImportProductRrpSerializer(serializers.Serializer):

    file = serializers.FileField(required=True)
    country = serializers.ChoiceField(choices=list(countries), required=True)
    rrp_currency = serializers.ChoiceField(
        choices=list(countries), required=True)
