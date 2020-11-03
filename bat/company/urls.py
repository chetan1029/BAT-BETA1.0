from django.urls import path, include

from rest_framework_nested import routers

from bat.company.views.setting import CompanyViewset, InvitationCreate

router = routers.SimpleRouter()
router.register('companies', CompanyViewset)

member_router = routers.NestedSimpleRouter(
    router, "companies", lookup='company')
# member_router.register('members', MemberViewset, basename='company-member')
member_router.register('invitations', InvitationCreate,
                       basename='company-invitation')

app_name = "company"
urlpatterns = router.urls

urlpatterns += [
    path('', include(member_router.urls)),
]
