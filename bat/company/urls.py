from django.urls import path, include

from rest_framework_nested import routers

from bat.company.views.setting import (
    CompanyViewset, InvitationCreate, CompanyPaymentTermsViewSet, BankViewSet, LocationViewSet)

router = routers.SimpleRouter()
router.register('companies', CompanyViewset)

member_router = routers.NestedSimpleRouter(
    router, "companies", lookup='company')
member_router.register('invitations', InvitationCreate,
                       basename='company-invitation')


payment_terms_router = routers.NestedSimpleRouter(
    router, "companies", lookup='company')
payment_terms_router.register('payment-terms', CompanyPaymentTermsViewSet,
                              basename='company-payment-terms')

bank_router = routers.NestedSimpleRouter(
    router, "companies", lookup='company')
bank_router.register('banks', BankViewSet,
                     basename='company-bank')

location_router = routers.NestedSimpleRouter(
    router, "companies", lookup='company')
location_router.register('locations', LocationViewSet,
                         basename='company-location')

app_name = "company"
urlpatterns = router.urls

urlpatterns += [
    path('', include(member_router.urls)),
    path('', include(payment_terms_router.urls)),
    path('', include(bank_router.urls)),
    path('', include(location_router.urls)),
]
