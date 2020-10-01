"""Froms related to user app."""

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field, Layout
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (AuthenticationForm, UserChangeForm,
                                       UserCreationForm)
from django.utils.translation import ugettext_lazy as _

User = get_user_model()


class LoginForm(AuthenticationForm):
    """Change label for username to Email / Username."""

    username = forms.CharField(label=_("Email / Username"))


class UserCreateForm(UserCreationForm):
    """User Form extending inbuild Django Auth."""

    class Meta:
        """Defining Model and fields."""

        model = User
        fields = (
            "first_name",
            "last_name",
            "username",
            "email",
            "password1",
            "password2",
        )

    def __init__(self, *args, **kwargs):
        """
        Call the __inti__ method before assigning.

        override form field properties and same thing we will use when we
        need to create two form like create and update
        """
        super().__init__(*args, **kwargs)
        self.fields["email"].label = _("Email address")
        self.fields["email"].required = True
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True

    def clean_email(self, *args, **kwargs):
        """
        Perform validation on Email.

        Fetch email field and perform validation like unique email in database
        or some other custom validation. you can raise error for perticular
        field from here that will be display as error on the formself.
        """
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            msg = _("Account with same email already exists.")
            raise forms.ValidationError(msg)
        return email


class UserUpdateForm(UserChangeForm):
    """UserForm form with field that need to edit in profile update."""

    class Meta:
        """Defining Model and fields."""

        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "profile_picture",
            "phone_number",
            "language",
            "timezone",
        )
        help_texts = {
            "username": _(
                "Username is unique for each account.\
             you can't change it."
            ),
            "email": _(
                "Email is unique for each account.\
             you can't change it"
            ),
        }

    def __init__(self, *args, **kwargs):
        """
        Call the __inti__ method before assigning.

        override form field properties and same thing we will use when we
        need to create two form like create and update
        """
        super().__init__(*args, **kwargs)
        self.fields["username"].disabled = True
        self.fields["email"].disabled = True
        self.fields["password"].widget = forms.HiddenInput()


class UserRolesForm(forms.Form):
    """User Roles Form."""

    roles = forms.CharField(widget=forms.HiddenInput)
    permissions = forms.CharField(widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        """Use Initiate the function tasks."""
        user = kwargs.pop("user", None)

        super(UserRolesForm, self).__init__(*args, **kwargs)
        # roles = [(role, ''.join(x.capitalize() + ' ' or '_' for x in role.split('_'))) for role in RolesManager.get_roles_names()]
        # self.fields['roles'].choices = roles

        helper = FormHelper()

        helper.layout = Layout(Field("roles"), Field("permissions"))

        if user and user.pk:
            self.initial["roles"] = ",".join(
                [role.get_name() for role in user.roles]
            )
            self.initial["permissions"] = ",".join(
                [
                    perm.replace("users.", "")
                    for perm in user.get_all_permissions()
                ]
            )

        helper.form_tag = False
        helper.include_media = False
        self.helper = helper
