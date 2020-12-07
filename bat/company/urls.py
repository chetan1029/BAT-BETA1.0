from django.urls import include, path
from rest_framework_nested import routers

from bat.company.views.comment import CompanyContractCommentsViewSet
from bat.company.views.company import (
    CompanyContractViewSet,
    CompanyCredentialViewSet,
    CompanyOrderDeliveryViewSet,
    CompanyOrderViewSet,
    CompanyProductViewSet,
    ComponentGoldenSampleViewSet,
    ComponentMeViewSet,
    ComponentPriceViewSet,
    CompanyOrderCaseViewSet,
    CompanyOrderInspectionViewSet,
    CompanyOrderDeliveryTestReportViewSet,
    CompanyOrderPaymentPaidViewSet,
    CompanyOrderPaymentViewSet
)
from bat.company.views.file import (CompanyContractFilesViewSet, ComponentMeFilesViewSet,
                                    CompanyOrderCaseFilesViewSet, CompanyOrderInspectionFilesViewSet,
                                    CompanyOrderDeliveryTestReportFilesViewSet, CompanyOrderPaymentPaidFilesViewSet,
                                    ComponentPriceFilesViewSet)
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
    CompanyInvitationViewSet,
)

from bat.company.views.file import (
    CompanyContractFilesViewSet, ComponentMeFilesViewSet, ComponentGoldenSampleFilesViewSet)

from bat.company.views.comment import (
    CompanyContractCommentsViewSet, )


router = routers.SimpleRouter()

# setting

router.register("companies", CompanyViewSet)

invitation_router = routers.NestedSimpleRouter(
    router, "companies", lookup="company"
)
invitation_router.register(
    "invite", InvitationCreate, basename="company-invitation"
)
member_router = routers.NestedSimpleRouter(
    router, "companies", lookup="company"
)
member_router.register("members", MemberViewSet, basename="company-members")
member_router.register(
    "invitations", CompanyInvitationViewSet, basename="company-invitations")


payment_terms_router = routers.NestedSimpleRouter(
    router, "companies", lookup="company"
)
payment_terms_router.register(
    "payment-terms",
    CompanyPaymentTermsViewSet,
    basename="company-payment-terms",
)

bank_router = routers.NestedSimpleRouter(router, "companies", lookup="company")
bank_router.register("bank", BankViewSet, basename="company-bank")

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
    "comments",
    CompanyContractCommentsViewSet,
    basename="company-contract-comments",
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
    "component-golden-samples",
    ComponentGoldenSampleViewSet,
    basename="company-golden-sample",
)

componentgoldensample_file_router = routers.NestedSimpleRouter(
    componentgoldesample_router, "component-golden-samples", lookup="object"
)

componentgoldensample_file_router.register(
    "files", ComponentGoldenSampleFilesViewSet, basename="company-component-golden-sample-files"
)

componentprice_router = routers.NestedSimpleRouter(
    router, "companies", lookup="company"
)
componentprice_router.register(
    "component-price", ComponentPriceViewSet, basename="component-price"
)

componentprice_file_router = routers.NestedSimpleRouter(
    componentprice_router, "component-price", lookup="object"
)

componentprice_file_router.register(
    "files", ComponentPriceFilesViewSet, basename="company-component-price-files"
)


companyproduct_router = routers.NestedSimpleRouter(
    router, "companies", lookup="company"
)
companyproduct_router.register(
    "company-product", CompanyProductViewSet, basename="company-product"
)

companyorder_router = routers.NestedSimpleRouter(
    router, "companies", lookup="company"
)
companyorder_router.register(
    "company-order", CompanyOrderViewSet, basename="company-order"
)

companyorderdelivery_router = routers.NestedSimpleRouter(
    router, "companies", lookup="company"
)
companyorderdelivery_router.register(
    "company-orderdelivery",
    CompanyOrderDeliveryViewSet,
    basename="company-orderdelivery",
)


company_order_case_router = routers.NestedSimpleRouter(
    router, "companies", lookup="company"
)
company_order_case_router.register(
    "company-order-case",
    CompanyOrderCaseViewSet,
    basename="company-order-case",
)

company_order_case_file_router = routers.NestedSimpleRouter(
    company_order_case_router, "company-order-case", lookup="object"
)

company_order_case_file_router.register(
    "files", CompanyOrderCaseFilesViewSet, basename="company-order-case-files"
)


company_order_inspection_router = routers.NestedSimpleRouter(
    router, "companies", lookup="company"
)
company_order_inspection_router.register(
    "company-order-inspection",
    CompanyOrderInspectionViewSet,
    basename="company-order-inspection",
)

company_order_inspection_file_router = routers.NestedSimpleRouter(
    company_order_inspection_router, "company-order-inspection", lookup="object"
)

company_order_inspection_file_router.register(
    "files", CompanyOrderInspectionFilesViewSet, basename="company-order-inspection-files"
)


company_order_delivery_testreport_router = routers.NestedSimpleRouter(
    router, "companies", lookup="company"
)
company_order_delivery_testreport_router.register(
    "company-order-delivery-testreport",
    CompanyOrderDeliveryTestReportViewSet,
    basename="company-order-delivery-testreport",
)

company_order_delivery_testreport_file_router = routers.NestedSimpleRouter(
    company_order_delivery_testreport_router, "company-order-delivery-testreport", lookup="object"
)

company_order_delivery_testreport_file_router.register(
    "files", CompanyOrderDeliveryTestReportFilesViewSet, basename="company-order-delivery-testreport-files"
)


company_order_payment_paid_router = routers.NestedSimpleRouter(
    router, "companies", lookup="company"
)
company_order_payment_paid_router.register(
    "company-order-payment-paid",
    CompanyOrderPaymentPaidViewSet,
    basename="company-order-payment-paid",
)

company_order_payment_paid_file_router = routers.NestedSimpleRouter(
    company_order_payment_paid_router, "company-order-payment-paid", lookup="object"
)

company_order_payment_paid_file_router.register(
    "files", CompanyOrderPaymentPaidFilesViewSet, basename="company-order-payment-paid-files"
)

company_order_payment_router = routers.NestedSimpleRouter(
    router, "companies", lookup="company"
)
company_order_payment_router.register(
    "company-order-payment",
    CompanyOrderPaymentViewSet,
    basename="company-order-payment",
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
    path("", include(componentgoldensample_file_router.urls)),
    path("", include(componentprice_router.urls)),
    path("", include(componentprice_file_router.urls)),
    path("", include(companyproduct_router.urls)),
    path("", include(companyorder_router.urls)),
    path("", include(companyorderdelivery_router.urls)),
    path("", include(company_order_case_router.urls)),
    path("", include(company_order_case_file_router.urls)),
    path("", include(company_order_inspection_router.urls)),
    path("", include(company_order_inspection_file_router.urls)),
    path("", include(company_order_delivery_testreport_router.urls)),
    path("", include(company_order_delivery_testreport_file_router.urls)),
    path("", include(company_order_payment_paid_router.urls)),
    path("", include(company_order_payment_paid_file_router.urls)),
    path("", include(company_order_payment_router.urls)),
]
