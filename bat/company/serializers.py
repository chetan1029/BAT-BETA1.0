from decimal import Decimal

from rest_framework import serializers

from django.utils.translation import ugettext_lazy as _

from invitations.utils import get_invitation_model

from bat.company.models import (Company, Member, CompanyPaymentTerms, Bank)
from bat.company.utils import get_list_of_roles, get_list_of_permissions


Invitation = get_invitation_model()


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

    def validate(self, data):
        """
        Check that start is before finish.
        """
        email = data['email']
        company_id = self.context.get("company_id", None)
        if company_id and email:
            if Member.objects.filter(
                company_id=int(company_id), user__email=email
            ).exists():
                raise serializers.ValidationError(
                    _("User already is your staff member."))
            else:
                invitations = Invitation.objects.filter(
                    email=email, company_detail__company_id=int(company_id)
                )
                if invitations.exists():
                    msg = _("Invitation already sent for this email.")
                    raise serializers.ValidationError(msg)

        return super().validate(data)


class CompanyPaymentTermsSerializer(serializers.ModelSerializer):
    """Serializer for payment terms."""

    class Meta:
        """Define field that we wanna show in the Json."""

        model = CompanyPaymentTerms
        fields = (
            "id",
            "title",
            "deposit",
            "on_delivery",
            "receiving",
            "remaining",
            "payment_days",
            "is_active",
            "extra_data",
        )
        read_only_fields = ("is_active", "extra_data", "remaining", "title")


class BankSerializer(serializers.ModelSerializer):
    """Serializer for bank."""

    class Meta:
        """Define field that we wanna show in the Json."""

        model = Bank
        fields = (
            "id",
            "name",
            "account_number",
            "iban",
            "swift_code",
            "currency",
            "is_active",
            "extra_data",
        )
        read_only_fields = ("is_active", "extra_data", "company ")
