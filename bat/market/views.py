from django.conf import settings

from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from bat.market import serializers
from bat.market.models import AmazonMarketplace


class AmazonMarketplaceViewsets(viewsets.ReadOnlyModelViewSet):
    queryset = AmazonMarketplace.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.AmazonMarketplaceSerializer


class AmazonAccountsAuthorization(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, company_pk=None, market_pk=None, **kwargs):

        print(company_pk, market_pk)
        '''
        1. send 
            - redirect to url - from ui -  AMAZON_SELLER_CENTRAL_AUTHORIZE_URL
        '''
        return Response(market_pk)


class AccountsReceiveAmazonCallback(APIView):
    '''
    receive amazon_callback_uri for confirmation
    '''

    def post(self, request, **kwargs):
        amazon_callback_uri = request.GET.get('amazon_callback_uri')
        return Response(amazon_callback_uri)
