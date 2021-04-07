from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, viewsets

from djmoney.settings import CURRENCY_CHOICES


class CurrencyChoicesViewSet(viewsets.ViewSet):

    def list(self, request):
        """
        list available currency choices in system
        """
        currency_choices = []
        for code, name in CURRENCY_CHOICES:
            currency_choices.append({
                "code": code,
                "name": name
            })
        return Response(currency_choices, status=status.HTTP_200_OK)
