from django.urls import path, include

from rest_framework_nested.routers import DefaultRouter

from bat.users.views import InvitationViewSet, RolesandPermissionsViewSet, UserViewsets

app_name = "users"

router = DefaultRouter()

router.register('user', UserViewsets)
router.register('invitations', InvitationViewSet)
router.register('role-permissions', RolesandPermissionsViewSet,
                basename="role-permissions")


urlpatterns = [
    path('', include(router.urls)),
]
