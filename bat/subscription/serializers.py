from rest_framework import serializers

from bat.serializersFields.serializers_fields import StatusField
from bat.subscription.models import Subscription, Plan
from bat.company.serializers import CompanySerializer


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = ("id", 'name', 'description', 'recurrence_period', 'recurrence_unit',
                  'cost', 'permission_list', 'available', 'visible',
                  'default', 'extra_data', 'meta_data', 'status', 'is_active',)
        read_only_fields = ("id", 'name', 'description', 'recurrence_period', 'recurrence_unit',
                            'cost', 'permission_list', 'available', 'visible',
                            'default', 'extra_data', 'meta_data', 'status', 'is_active',)


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
