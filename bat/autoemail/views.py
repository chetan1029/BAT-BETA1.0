from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated

from dry_rest_permissions.generics import DRYPermissions

from bat.autoemail import serializers
from bat.autoemail.models import EmailCampaign, EmailQueue


class EmailCampaignViewsets(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet
):
    queryset = EmailCampaign.objects.all()
    serializer_class = serializers.EmailCampaignSerializer
    permission_classes = (IsAuthenticated,)

    def filter_queryset(self, queryset):
        company_id = self.kwargs.get("company_pk", None)
        queryset = super().filter_queryset(queryset)
        return queryset.filter(company__id=company_id).order_by("-create_date")


class EmailQueueViewsets(
    viewsets.ReadOnlyModelViewSet
):
    queryset = EmailQueue.objects.all()
    serializer_class = serializers.EmailQueueSerializer
    permission_classes = (IsAuthenticated,)

    def filter_queryset(self, queryset):
        company_id = self.kwargs.get("company_pk", None)
        queryset = super().filter_queryset(queryset)
        return queryset.filter(emailcampaign__company__id=company_id).order_by("-create_date")

