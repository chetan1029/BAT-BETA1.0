from django.urls import path, include

from rest_framework_nested.routers import DefaultRouter

from bat.users.views import InvitationViewSet, RolesandPermissionsViewSet
# from bat.users.views import (
#     user_detail_view,
#     user_redirect_view,
#     user_update_view,
# )

router = DefaultRouter()

router.register('invitations', InvitationViewSet)
router.register('role-permissions', RolesandPermissionsViewSet,
                basename="role-permissions")
app_name = "users"


urlpatterns = [
    path('', include(router.urls)),
    # path("~redirect/", view=user_redirect_view, name="redirect"),
    # path("~update/", view=user_update_view, name="update"),
    # path("<str:username>/", view=user_detail_view, name="detail"),

]
