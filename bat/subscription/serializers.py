from rest_framework import serializers

from bat.company.serializers import CompanySerializer
from bat.serializersFields.serializers_fields import MoneySerializerField, StatusField
from bat.subscription.constants import RECURRENCE_UNIT_CHOICES
from bat.subscription.models import Feature, Plan, PlanQuota, Quota, Subscription


class QuotaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quota
        fields = (
            "id",
            "codename",
            "name",
            "unit",
            "description",
            "is_boolean",
            "url",
        )
        read_only_fields = (
            "id",
            "codename",
            "name",
            "unit",
            "description",
            "is_boolean",
            "url",
        )


class PlanQuotaSerializer(serializers.ModelSerializer):
    quota = QuotaSerializer(read_only=True)
    available_quota = serializers.SerializerMethodField()
    used_quota = serializers.SerializerMethodField()

    class Meta:
        model = PlanQuota
        fields = ("id", "value", "used_quota", "available_quota", "quota")
        read_only_fields = (
            "id",
            "value",
            "used_quota",
            "available_quota",
            "quota",
        )

    def get_available_quota(self, obj):
        feature = Feature.objects.filter(
            plan_quota_id=obj.id, company_id=self.context.get("company_id")
        ).first()
        if feature:
            return feature.consumption
        return 0

    def get_used_quota(self, obj):
        feature = Feature.objects.filter(
            plan_quota_id=obj.id, company_id=self.context.get("company_id")
        ).first()
        if feature:
            return obj.value - feature.consumption
        return 0


class PlanSerializer(serializers.ModelSerializer):
    plan_quotas = PlanQuotaSerializer(read_only=True, many=True)
    cost = MoneySerializerField()
    recurrence_unit = serializers.CharField(
        source="get_recurrence_unit_display"
    )

    class Meta:
        model = Plan
        fields = (
            "id",
            "name",
            "description",
            "recurrence_period",
            "recurrence_unit",
            "cost",
            "permission_list",
            "available",
            "visible",
            "default",
            "extra_data",
            "meta_data",
            "status",
            "is_active",
            "plan_quotas",
        )
        read_only_fields = (
            "id",
            "name",
            "description",
            "recurrence_period",
            "recurrence_unit",
            "cost",
            "permission_list",
            "available",
            "visible",
            "default",
            "extra_data",
            "meta_data",
            "status",
            "is_active",
            "plan_quotas",
        )


class SubscriptionSerializer(serializers.ModelSerializer):
    status = StatusField()
    plan = PlanSerializer(read_only=True)
    company = CompanySerializer(read_only=True)

    class Meta:
        model = Subscription
        fields = (
            "id",
            "company",
            "plan",
            "billing_start_date",
            "billing_end_date",
            "last_billing_date",
            "next_billing_date",
            "status",
            "is_active",
        )
        read_only_fields = (
            "id",
            "company",
            "plan",
            "billing_start_date",
            "billing_end_date",
            "last_billing_date",
            "next_billing_date",
            "status",
            "is_active",
        )
