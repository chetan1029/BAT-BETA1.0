from rest_framework import viewsets

from bat.subscription.models import Subscription
from bat.subscription.serializers import SubscriptionSerializer


class SubscriptionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
