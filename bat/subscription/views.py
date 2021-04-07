from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from bat.subscription.models import Subscription
from bat.subscription.serializers import SubscriptionSerializer
from bat.company.utils import get_member


class SubscriptionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = (IsAuthenticated,)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        company_id = self.kwargs.get("company_pk", None)
        context["company_id"] = company_id
        return context

    def filter_queryset(self, queryset):
        """
        filter subscription for current company.
        """
        company_id = self.kwargs.get("company_pk", None)
        _member = get_member(
            company_id=company_id,
            user_id=self.request.user.id,
        )
        queryset = super().filter_queryset(queryset)
        queryset = queryset.filter(company_id=company_id)
        return queryset
