from django_filters.rest_framework import filters, filterset

from bat.autoemail.constants import ORDER_EMAIL_PARENT_STATUS
from bat.autoemail.models import EmailQueue


class EmailQueueFilter(filterset.FilterSet):
    """
    provide filter set to Email Queue
    """

    status = filters.CharFilter(field_name="status", method="filter_by_status")

    def filter_by_status(self, qs, name, value):
        if value == "reattempted-reviews":
            return qs.filter(
                emailcampaign__send_optout=True,
                amazonorder__amazon_review=True,
            ).distinct()
        else:
            return qs.filter(
                status__name__iexact=value,
                status__parent__name=ORDER_EMAIL_PARENT_STATUS,
            ).distinct()

    class Meta:
        model = EmailQueue
        fields = ["emailcampaign_id"]
