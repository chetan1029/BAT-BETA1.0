from decimal import Decimal

from rest_framework import serializers

from django.utils.translation import ugettext_lazy as _

from invitations.utils import get_invitation_model

from bat.company.models import Company, Member, CompanyPaymentTerms
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


class CompanyPaymentTermsSerializer(serializers.HyperlinkedModelSerializer):
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

    def create(self, validated_data):
        """Append extra data in validated data by overriding."""
        deposit = validated_data.get("deposit", 0)
        on_delivery = validated_data.get("on_delivery", 0)
        receiving = validated_data.get("receiving", 0)
        remaining = Decimal(100) - (
            Decimal(deposit) + Decimal(on_delivery) + Decimal(receiving)
        )
        payment_days = validated_data.get("payment_days", 0)
        title = (
            "PAY"
            + str(deposit)
            + "-"
            + str(on_delivery)
            + "-"
            + str(receiving)
            + "-"
            + str(remaining)
            + "-"
            + str(payment_days)
            + "Days"
        )
        return CompanyPaymentTerms.objects.create(
            title=title, remaining=remaining, **validated_data
        )

    def update(self, instance, validated_data):
        """Append extra data in validated data by overriding."""
        instance.deposit = validated_data.get("deposit", instance.deposit)
        instance.on_delivery = validated_data.get(
            "on_delivery", instance.on_delivery
        )
        instance.receiving = validated_data.get(
            "receiving", instance.receiving
        )
        remaining = Decimal(100) - (
            Decimal(instance.deposit)
            + Decimal(instance.on_delivery)
            + Decimal(instance.receiving)
        )
        instance.payment_days = validated_data.get(
            "payment_days", instance.payment_days
        )
        instance.title = (
            "PAY"
            + str(instance.deposit)
            + "-"
            + str(instance.on_delivery)
            + "-"
            + str(instance.receiving)
            + "-"
            + str(remaining)
            + "-"
            + str(instance.payment_days)
            + "Days"
        )
        instance.remaining = remaining
        instance.save()
        return instance
