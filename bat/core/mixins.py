"""We put all the mixing into the core app."""
from __future__ import unicode_literals

from bat.core.decorators import has_permission_decorator, has_role_decorator
from django.contrib import messages
from django.db.models.deletion import ProtectedError
from django.http import HttpResponseRedirect


class HasRoleMixin(object):
    """Check for role."""

    allowed_roles = []
    redirect_to_login = None

    def dispatch(self, request, *args, **kwargs):
        """Validate."""
        roles = self.allowed_roles
        return has_role_decorator(
            roles, redirect_to_login=self.redirect_to_login
        )(super(HasRoleMixin, self).dispatch)(request, *args, **kwargs)


class HasPermissionsMixin(object):
    """Check for permissions."""

    required_permission = ""
    redirect_to_login = None

    def dispatch(self, request, *args, **kwargs):
        """Validate."""
        permission = self.required_permission
        return has_permission_decorator(
            permission, redirect_to_login=self.redirect_to_login
        )(super(HasPermissionsMixin, self).dispatch)(request, *args, **kwargs)


class DeleteMixin:
    """
    Mixing to use while deleting data.

    I found some time we have to use same set of delete method for many CBV so
    I decided to make a mixin and pass that mixin to all delete views.
    """

    def delete(self, request, *args, **kwargs):
        """Delete method to define error messages."""
        obj = self.get_object()
        get_success_url = self.get_success_url()
        get_error_url = self.get_error_url()
        try:
            try:
                if self.request.is_archived:
                    obj.is_active = False
                    obj.save()
                elif self.request.is_restored:
                    obj.is_active = True
                    obj.save()
                else:
                    obj.delete()
            except AttributeError:
                obj.delete()
            messages.success(self.request, self.success_message % obj.__dict__)
            return HttpResponseRedirect(get_success_url)
        except ProtectedError:
            messages.warning(self.request, self.protected_error % obj.__dict__)
            return HttpResponseRedirect(get_error_url)
