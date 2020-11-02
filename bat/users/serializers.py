
from rest_auth.registration.serializers import RegisterSerializer
from invitations.utils import get_invitation_model

Invitation = get_invitation_model()


class RestAuthRegisterSerializer(RegisterSerializer):
    def custom_signup(self, request, user):
        '''
        save extra_data to user
        '''
        extra_data = {}
        # # Check if this user has accpeted invitations or even have
        # # any invitation. we will signup and forward user.
        invitations = Invitation.objects.filter(email=user.email)
        print("invitations : ", invitations)
        if invitations.exists():
            extra_data["step"] = "2"
            extra_data["step_detail"] = "account setup"
        else:
            extra_data["step"] = "1"
            extra_data["step_detail"] = "user signup"
        user.extra_data = extra_data
        user.save()
        print('user in RestAuthRegisterSerializer :', user)
