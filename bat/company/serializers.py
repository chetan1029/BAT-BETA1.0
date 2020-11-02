from rest_framework import serializers

from bat.company.models import Company


class CompanySerializer(serializers.ModelSerializer):

    class Meta:
        model = Company
        fields = "__all__"
        # read_only_fields = ('owner',)
