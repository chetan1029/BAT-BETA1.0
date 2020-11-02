from rest_framework import serializers

from bat.company.models import Company, Member


class CompanySerializer(serializers.ModelSerializer):

    class Meta:
        model = Company
        fields = "__all__"
        # read_only_fields = ('owner',)


class MemberSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    # roles = serializers.ChoiceField(choices=, required=True)
    # permissions = serializers.ChoiceField(choices=, required=True)

    class Meta:
        model = Member
        fields = ('job_title', 'first_name', 'last_name', 'email',)
        # read_only_fields = ('owner',)
