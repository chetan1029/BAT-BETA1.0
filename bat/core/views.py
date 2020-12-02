from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, viewsets

from djmoney.settings import CURRENCY_CHOICES


class CurrencyChoicesViewSet(viewsets.ViewSet):

    def list(self, request):
        """
        list available currency choices in system
        """
        return Response(CURRENCY_CHOICES, status=status.HTTP_200_OK)
