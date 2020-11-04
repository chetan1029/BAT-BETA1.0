from django.urls import path, include

from rest_framework_nested.routers import DefaultRouter

from bat.users.views import InvitationViewSet, RolesandPermissionsViewSet, UserViewsets
# from bat.users.views import (
#     user_detail_view,
#     user_redirect_view,
#     user_update_view,
# )
app_name = "users"

router = DefaultRouter()

router.register('users', UserViewsets)
router.register('invitations', InvitationViewSet)
router.register('role-permissions', RolesandPermissionsViewSet,
                basename="role-permissions")


urlpatterns = [
    path('', include(router.urls)),
]
