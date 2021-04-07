from rest_framework import serializers

from bat.serializersFields.serializers_fields import StatusField
from bat.subscription.models import Subscription, Plan, Quota, PlanQuota, Feature
from bat.company.serializers import CompanySerializer


class QuotaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quota
        fields = ("id", 'codename', 'name', 'unit', 'description',
                  'is_boolean', 'url',)
        read_only_fields = ("id", 'codename', 'name', 'unit', 'description',
                            'is_boolean', 'url',)


class PlanQuotaSerializer(serializers.ModelSerializer):
    quota = QuotaSerializer(read_only=True)
    available_quota = serializers.SerializerMethodField()

    class Meta:
        model = PlanQuota
        fields = ("id", 'value', 'available_quota', 'quota',)
        read_only_fields = ("id", 'value', 'available_quota', 'quota',)

    def get_available_quota(self, obj):
        feature = Feature.objects.filter(
            plan_quota_id=obj.id, company_id=self.context.get("company_id")).first()
        if feature:
            return feature.consumption
        return 0


class PlanSerializer(serializers.ModelSerializer):
    plan_quotas = PlanQuotaSerializer(read_only=True, many=True)

    class Meta:
        model = Plan
        fields = ("id", 'name', 'description', 'recurrence_period', 'recurrence_unit',
                  'cost', 'permission_list', 'available', 'visible',
                  'default', 'extra_data', 'meta_data', 'status', 'is_active', 'plan_quotas',)
        read_only_fields = ("id", 'name', 'description', 'recurrence_period', 'recurrence_unit',
                            'cost', 'permission_list', 'available', 'visible',
                            'default', 'extra_data', 'meta_data', 'status', 'is_active', 'plan_quotas')


class SubscriptionSerializer(serializers.ModelSerializer):
    status = StatusField()
    plan = PlanSerializer(read_only=True)
    company = CompanySerializer(read_only=True)

    class Meta:
        model = Subscription
        fields = ("id", 'company', 'plan', 'billing_start_date', 'billing_end_date',
                  'last_billing_date', 'next_billing_date', 'status', 'is_active',)
        read_only_fields = ("id", 'company', 'plan', 'billing_start_date', 'billing_end_date',
                            'last_billing_date', 'next_billing_date', 'status', 'is_active',)
