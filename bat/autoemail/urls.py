from django.urls import include, path
from rest_framework_nested import routers

from bat.autoemail.views import (
    EmailCampaignViewsets,
    EmailChartDataAPIView,
    EmailQueueViewsets,
    EmailTemplateViewsets,
)
from bat.company.urls import router

email_campaign_router = routers.NestedSimpleRouter(
    router, "companies", lookup="company"
)
email_campaign_router.register(
    "email-campaign", EmailCampaignViewsets, basename="company-email-campaign"
)

email_queue_router = routers.NestedSimpleRouter(
    router, "companies", lookup="company"
)
email_queue_router.register(
    "email-queue", EmailQueueViewsets, basename="company-email-queue"
)

email_template_router = routers.NestedSimpleRouter(
    router, "companies", lookup="company"
)
email_template_router.register(
    "email-template", EmailTemplateViewsets, basename="company-email-template"
)


app_name = "autoemail"

urlpatterns = [
    path("", include(email_campaign_router.urls)),
    path("", include(email_template_router.urls)),
    path("", include(email_queue_router.urls)),
    path(
        "companies/<company_pk>/email-chart-data/",
        EmailChartDataAPIView.as_view(),
        name="email-chart-data",
    ),
]
