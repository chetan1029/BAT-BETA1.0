from rest_framework import serializers

from bat.company.models import Company, Member
from bat.company.utils import get_list_of_roles, get_list_of_permissions


class CompanySerializer(serializers.ModelSerializer):

    class Meta:
        model = Company
        fields = "__all__"
        # read_only_fields = ('owner',)


class InvitationDataSerializer(serializers.Serializer):
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    job_title = serializers.CharField(required=True)
    role = serializers.ChoiceField(choices=get_list_of_roles(), required=True)
    permissions = serializers.MultipleChoiceField(
        choices=get_list_of_permissions(), required=True)


# class MemberSerializer(serializers.ModelSerializer):
#     first_name = serializers.CharField(required=True)
#     last_name = serializers.CharField(required=True)
#     email = serializers.EmailField(required=True)
#     # roles = serializers.ChoiceField(choices=, required=True)
#     # permissions = serializers.ChoiceField(choices=, required=True)

#     class Meta:
#         model = Member
#         fields = ('job_title', 'first_name', 'last_name', 'email',)
#         # read_only_fields = ('owner',)
