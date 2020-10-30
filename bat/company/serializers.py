"""Serialize django model for reach frontend."""

from decimal import Decimal

from bat.company.models import CompanyPaymentTerms
from rest_framework import serializers


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
