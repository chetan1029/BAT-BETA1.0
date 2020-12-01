from django.urls import include, path
from rest_framework_nested import routers

from bat.company.views.company import (
    CompanyContractViewSet,
    CompanyCredentialViewSet,
    ComponentGoldenSampleViewSet,
    ComponentMeViewSet
)
from bat.company.views.setting import (
    BankViewSet,
    CompanyPaymentTermsViewSet,
    CompanyViewSet,
    HsCodeBoxViewSet,
    InvitationCreate,
    LocationViewSet,
    MemberViewSet,
    PackingBoxViewSet,
    TaxBoxViewSet,
)

from bat.company.views.file import (
    CompanyContractFilesViewSet, ComponentMeFilesViewSet)

from bat.company.views.comment import (
    CompanyContractCommentsViewSet, )


router = routers.SimpleRouter()

# setting

router.register("companies", CompanyViewSet)

invitation_router = routers.NestedSimpleRouter(
    router, "companies", lookup="company"
)
invitation_router.register(
    "invitations", InvitationCreate, basename="company-invitation"
)
member_router = routers.NestedSimpleRouter(
    router, "companies", lookup="company"
)
member_router.register("members", MemberViewSet, basename="company-members")


payment_terms_router = routers.NestedSimpleRouter(
    router, "companies", lookup="company"
)
payment_terms_router.register(
    "payment-terms",
    CompanyPaymentTermsViewSet,
    basename="company-payment-terms",
)

bank_router = routers.NestedSimpleRouter(router, "companies", lookup="company")
bank_router.register("banks", BankViewSet, basename="company-bank")

location_router = routers.NestedSimpleRouter(
    router, "companies", lookup="company"
)
location_router.register(
    "locations", LocationViewSet, basename="company-location"
)


packingbox_router = routers.NestedSimpleRouter(
    router, "companies", lookup="company"
)
packingbox_router.register(
    "packing-boxs", PackingBoxViewSet, basename="company-packingbox"
)

hscode_router = routers.NestedSimpleRouter(
    router, "companies", lookup="company"
)
hscode_router.register("hscodes", HsCodeBoxViewSet, basename="company-hscode")

tax_router = routers.NestedSimpleRouter(router, "companies", lookup="company")
tax_router.register("taxes", TaxBoxViewSet, basename="company-tax")


# company

contract_router = routers.NestedSimpleRouter(
    router, "companies", lookup="company"
)
contract_router.register(
    "contracts", CompanyContractViewSet, basename="company-contract"
)


contract_file_router = routers.NestedSimpleRouter(
    contract_router, "contracts", lookup="object"
)

contract_file_router.register(
    "files", CompanyContractFilesViewSet, basename="company-contract-files"
)


contract_comment_router = routers.NestedSimpleRouter(
    contract_router, "contracts", lookup="object"
)

contract_comment_router.register(
    "comments", CompanyContractCommentsViewSet, basename="company-contract-comments"
)


credentail_router = routers.NestedSimpleRouter(
    router, "companies", lookup="company"
)
credentail_router.register(
    "credential", CompanyCredentialViewSet, basename="company-credential"
)

componentme_router = routers.NestedSimpleRouter(
    router, "companies", lookup="company"
)
componentme_router.register(
    "component-me", ComponentMeViewSet, basename="company-me"
)

componentme_file_router = routers.NestedSimpleRouter(
    componentme_router, "component-me", lookup="object"
)

componentme_file_router.register(
    "files", ComponentMeFilesViewSet, basename="company-component-me-files"
)

componentgoldesample_router = routers.NestedSimpleRouter(
    router, "companies", lookup="company"
)
componentgoldesample_router.register(
    "component-golden-sample",
    ComponentGoldenSampleViewSet,
    basename="company-golden-sample",
)

app_name = "company"
urlpatterns = router.urls

urlpatterns += [
    path("", include(invitation_router.urls)),
    path("", include(member_router.urls)),
    path("", include(payment_terms_router.urls)),
    path("", include(bank_router.urls)),
    path("", include(location_router.urls)),
    path("", include(packingbox_router.urls)),
    path("", include(hscode_router.urls)),
    path("", include(tax_router.urls)),
    path("", include(contract_router.urls)),
    path("", include(contract_file_router.urls)),
    path("", include(credentail_router.urls)),
    path("", include(componentme_router.urls)),
    path("", include(componentme_file_router.urls)),
    path("", include(contract_comment_router.urls)),
    path("", include(componentgoldesample_router.urls)),
]
