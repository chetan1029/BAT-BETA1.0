from django.urls import path
from rest_framework import routers

from bat.company.urls import router as company_router
from bat.market.views import AmazonMarketplaceViewsets, AmazonAccountsAuthorization

router = routers.SimpleRouter()

router.register('amazon-marketplaces', AmazonMarketplaceViewsets)

app_name = "market"

urlpatterns = router.urls

urlpatterns = urlpatterns + [
    path('companies/<company_pk>/amazon-marketplaces/<market_pk>/authorize',
         AmazonAccountsAuthorization.as_view()),
]
