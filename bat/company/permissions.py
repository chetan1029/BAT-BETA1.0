from rest_framework import permissions
from rolepermissions.checkers import has_permission


class CompanyPaymentTermsPermission(permissions.DjangoModelPermissions):
    """
    check permission based on request and user
    """

    def has_permission(self, request, view):
        print("in CompanyPaymentTermsPermission")
        if not request.user or (
           not request.user.is_authenticated and self.authenticated_users_only):
            return False

        queryset = self._queryset(view)
        perms = self.get_required_permissions(request.method, queryset.model)

        # return request.user.has_perms(perms)
        print(view.kwargs, ": kwargs")
        print(perms, ": perms")
        print(request.resolver_match.kwargs.get('company_pk'), ": company_pk")
        return True
