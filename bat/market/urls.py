from django.urls import path
from rest_framework import routers

from bat.company.urls import router as company_router
from bat.market.views import AmazonMarketplaceViewsets, AmazonAccountsAuthorization, AccountsReceiveAmazonCallback

router = routers.SimpleRouter()

router.register('amazon-marketplaces', AmazonMarketplaceViewsets)

app_name = "market"

urlpatterns = router.urls

urlpatterns = urlpatterns + [
    path('companies/<company_pk>/amazon-marketplaces/<market_pk>/authorize/',
         AmazonAccountsAuthorization.as_view()),
    path('auth-callback/amazon-marketplaces/',
         AccountsReceiveAmazonCallback.as_view()),
]
