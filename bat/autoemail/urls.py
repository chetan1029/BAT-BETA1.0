from django.urls import include, path
from rest_framework_nested import routers

from bat.company.urls import router
from bat.autoemail.views import EmailCampaignViewsets, EmailQueueViewsets, DashboardAPIView


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


app_name = "autoemail"

urlpatterns = [
    path("", include(email_campaign_router.urls)),
    path("", include(email_queue_router.urls)),
    path("companies/<company_pk>/email-campaign-dashboard/", DashboardAPIView.as_view(), name="email-campaign-dashboard")
]
