from django.urls import path, include

from rest_framework_nested import routers

from bat.company.views.setting import CompanyViewset, InvitationCreate, CompanyPaymentTermsViewSet

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


app_name = "company"
urlpatterns = router.urls

urlpatterns += [
    path('', include(member_router.urls)),
    path('', include(payment_terms_router.urls)),
]
