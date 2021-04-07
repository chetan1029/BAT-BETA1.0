from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from django.contrib.auth import get_user_model

from invitations.utils import get_invitation_model

from bat.users.forms import UserChangeForm, UserCreationForm

User = get_user_model()
Invitation = get_invitation_model()

admin.site.site_header = "BAT Admin"
admin.site.site_title = "BAT Admin Portal"
admin.site.index_title = "Welcome to BAT admin Portal"


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):

    form = UserChangeForm
    add_form = UserCreationForm
