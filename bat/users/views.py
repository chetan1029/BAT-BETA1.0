"""View class and functions for user app."""

import logging
from collections import OrderedDict

from bat.company.models import Member
from bat.users.forms import UserCreateForm, UserRolesForm, UserUpdateForm
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.translation import LANGUAGE_SESSION_KEY, activate
from django.views.generic import CreateView, ListView, TemplateView, UpdateView
from reversion.views import RevisionMixin
from rolepermissions.mixins import HasPermissionsMixin
from rolepermissions.permissions import revoke_permission
from rolepermissions.roles import RolesManager, assign_role, clear_roles

logger = logging.getLogger(__name__)
User = get_user_model()


# Create Mixins
class UserMenuMixin:
    """Mixing For Payment Terms Menu."""

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        context["active_menu"] = {"dashboard": "global", "menu1": "my-profile"}
        return context


# Create your views here.
class SignUp(CreateView):
    """View Class for User Signup."""

    form_class = UserCreateForm
    success_url = reverse_lazy("company:account_setup")
    template_name = "user/signup.html"

    def form_valid(self, form):
        """Set Langauge of the submited form and set it as current."""
        self.object = form.save(commit=False)
        extra_data = {}
        extra_data["step"] = "1"
        extra_data["step_detail"] = "user signup"
        self.object.extra_data = extra_data
        self.object.save()
        to_return = super().form_valid(form)
        # Login the user
        user = authenticate(
            username=form.cleaned_data["username"],
            password=form.cleaned_data["password1"],
        )
        login(self.request, user)
        return to_return

    def get(self, request, *args, **kwargs):
        """
        Forward loggedin user to dashboard.

        We are using get method because when url called this method called and
        we can access user instance with request and check user is loggedin or
        not.
        """
        if self.request.user.is_authenticated:
            return HttpResponseRedirect("/dashboard/")
        return super().get(request, *args, **kwargs)


class SignUpClose(TemplateView):
    """View Class for User Signup Close."""

    template_name = "user/signup_close.html"

    def get(self, request, *args, **kwargs):
        """
        Forward loggedin user to dashboard.

        We are using get method because when url called this method called and
        we can access user instance with request and check user is loggedin or
        not.
        """
        if self.request.user.is_authenticated:
            return HttpResponseRedirect("/dashboard/")
        return super().get(request, *args, **kwargs)


class CustomLoginView(LoginView):
    """View Class for User Signup Close."""

    template_name = "user/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        """
        Forward loggedin user to dashboard.

        We are using get method because when url called this method called
        after logged in we will set Langauge and Timezone as user profile
        selected one.
        """
        user = self.request.user
        # Set User langaunge as default language
        user_language = user.language
        activate(user_language)
        self.request.session[LANGUAGE_SESSION_KEY] = user_language
        # Set user timezone
        self.request.session["user_timezone"] = user.timezone
        # Set Member profile session if user have just one active
        # member profile
        try:
            member = Member.objects.get(user=user, is_active=True)
            self.request.session["member_id"] = member.pk
        except (ObjectDoesNotExist, MultipleObjectsReturned):
            pass
        return reverse_lazy("core:dashboard")


class UpdateProfile(
    LoginRequiredMixin,
    RevisionMixin,
    SuccessMessageMixin,
    UserMenuMixin,
    UpdateView,
):
    """View Class for User Profile Update."""

    form_class = UserUpdateForm
    model = User
    success_url = reverse_lazy("accounts:update_profile")
    template_name = "user/profile.html"
    success_message = "Your profile was updated successfully"

    def form_valid(self, form):
        """Set Langauge of the submited form and set it as current."""
        user_language = self.object.language
        # Set User langaunge as default language
        activate(user_language)
        self.request.session[LANGUAGE_SESSION_KEY] = user_language
        # Set user timezone
        self.request.session["user_timezone"] = self.object.timezone
        return super().form_valid(form)

    def get_object(self):
        """
        User profile Update.

        UpdateView only allowed to use in view after passing pk in the url or
        pass it via get_object and we are passing currently loggedin user query
        via get_object.
        """
        return self.request.user

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        context["active_menu"].update({"menu2": "update-profile"})
        return context


class CustomPasswordChangeView(UserMenuMixin, PasswordChangeView):
    """View Class for Password Reset."""

    template_name = "user/password_change_form.html"
    success_url = "done"

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        context["active_menu"].update({"menu2": "password-change"})
        return context

    def post(self, request, *args, **kwargs):
        """Get data when posted and setup custom context."""
        context = self.get_context_data(**kwargs)
        context["success"] = True
        return self.render_to_response(context)


class RolesView(HasPermissionsMixin, LoginRequiredMixin, ListView):
    """User roles view."""

    required_permission = "view_roles"
    model = User
    template_name = "user/roles/list.html"

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        context["active_menu"] = {"dashboard": "global", "menu1": "roles"}
        return context


class RoleEditView(HasPermissionsMixin, LoginRequiredMixin, TemplateView):
    """Edit user roles."""

    required_permission = "edit_roles"
    template_name = "user/roles/edit.html"
    success_message = "User roles and permissions were updated successfully"
    success_url = reverse_lazy("accounts:list_roles")

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        user_id = kwargs.get("pk", None)
        context = super(RoleEditView, self).get_context_data(**kwargs)

        context["active_menu"] = {"dashboard": "global", "menu1": "roles"}
        role_user = get_object_or_404(User, pk=user_id)
        context["role_user"] = role_user
        all_roles = OrderedDict()

        users_permissions = role_user.get_all_permissions()
        context["users_permissions"] = users_permissions

        for role in RolesManager.get_roles():
            role_name = role.get_name()
            all_roles[role_name] = {
                "display_name": "".join(
                    x.capitalize() + " " or "_" for x in role_name.split("_")
                ),
                "permissions": {
                    perm: "".join(
                        x.capitalize() + " " or "_" for x in perm.split("_")
                    )
                    for perm in role.permission_names_list()
                },
            }

        context["available_roles"] = all_roles

        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context["form"] = UserRolesForm(user=context["role_user"])
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        form = UserRolesForm(request.POST, user=context["role_user"])
        context["form"] = form

        if form.is_valid():
            role_user = context["role_user"]
            clear_roles(role_user)
            # assign new roles
            roles = form.cleaned_data.get("roles", "")
            roles = roles.split(",")

            perms = form.cleaned_data.get("permissions", "")
            perms = perms.split(",")

            for role in roles:
                assign_role(role_user, role)
                role_obj = RolesManager.retrieve_role(role)
                # remove unneccesary permissions
                for perm in role_obj.permission_names_list():
                    if perm not in perms:
                        revoke_permission(role_user, perm)
            messages.success(request, self.success_message)
            return HttpResponseRedirect(self.success_url)
        return self.render_to_response(context)


class MyCompaniesView(LoginRequiredMixin, UserMenuMixin, TemplateView):
    """User roles view."""

    template_name = "user/my_companies.html"
    success_url = reverse_lazy("core:dashboard")

    def post(self, request, *args, **kwargs):
        """Post member id to this view."""
        context = self.get_context_data(**kwargs)
        member_id = request.POST.get("member_id", False)
        if member_id:
            request.session["member_id"] = member_id
            return HttpResponseRedirect(self.success_url)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        context["active_menu"].update({"menu2": "my-companies"})
        context["active_members"] = Member.objects.filter(
            user=self.request.user, is_active=True
        )
        context["inactive_members"] = Member.objects.filter(
            user=self.request.user, is_active=False, invitation_accepted=True
        )
        context["pending_invitations"] = Member.objects.filter(
            user=self.request.user, is_active=False, invitation_accepted=False
        )
        return context


class CompanyLoginView(LoginRequiredMixin, UserMenuMixin, TemplateView):
    """Company Login view."""

    template_name = "user/company_login.html"
    success_url = reverse_lazy("core:dashboard")

    def post(self, request, *args, **kwargs):
        """Post member id to this view."""
        context = self.get_context_data(**kwargs)
        member_id = request.POST.get("member_id", False)
        if member_id:
            request.session["member_id"] = member_id
            return HttpResponseRedirect(self.success_url)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        context["active_menu"].update({"menu2": "my-companies"})
        context["member_list"] = Member.objects.filter(
            user=self.request.user, is_active=True
        )
        return context
