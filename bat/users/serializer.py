from rest_auth.registration.serializers import RegisterSerializer


class RestAuthRegisterSerializer(RegisterSerializer):
    def custom_signup(self, request, user):
        '''
        save extra_data
        '''
        extra_data = {}
        # # Check if this user has accpeted invitations or even have
        # # any invitation. we will signup and forward user.
        # invitations = Invitation.objects.filter(email=self.object.email)
        # if invitations.exists():
        #     extra_data["step"] = "2"
        #     extra_data["step_detail"] = "account setup"
        # else:
        #     extra_data["step"] = "1"
        #     extra_data["step_detail"] = "user signup"
        extra_data["step"] = "1"
        extra_data["step_detail"] = "user signup"
        user.extra_data = extra_data
        pass
