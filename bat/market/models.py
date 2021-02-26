from django.db import models
from django_countries.fields import CountryField
from django.contrib.auth import get_user_model


from bat.company.models import Company

User = get_user_model()


class AmazonMarketplace(models.Model):
    name = models.CharField(max_length=255, null=True)
    country = CountryField()
    marketplaceId = models.CharField(max_length=255)


class AmazonAccounts(models.Model):
    marketplace = models.ForeignKey(AmazonMarketplace, on_delete=models.PROTECT)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    selling_partner_id = models.CharField(max_length=255, null=True)
    mws_auth_token = models.CharField(max_length=255, null=True)
    spapi_oauth_code = models.CharField(max_length=255, null=True)
    access_token = models.CharField(max_length=255, null=True)
    expires_at = models.DateTimeField(null=True)
    refresh_token = models.CharField(max_length=255, null=True)
