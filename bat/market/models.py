import os
import uuid

from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _

from django_countries.fields import CountryField

from bat.company.models import Company
from bat.market.constants import AMAZON_REGIONS_CHOICES, EUROPE

User = get_user_model()


def file_name(instance, filename):
    """Change name of image."""
    name, extension = os.path.splitext(filename)
    return "files/marketplace/{0}_{1}{2}".format(
        str(name),
        uuid.uuid4(),
        extension,
    )


class AmazonMarketplace(models.Model):
    name = models.CharField(verbose_name=_("Name"), max_length=255, null=True, blank=True)
    country = CountryField(verbose_name=_("Country"))
    # TODO set countries_flag_url in CountryField for market icon
    marketplaceId = models.CharField(verbose_name=_("MarketplaceId"), max_length=255)
    region = models.CharField(verbose_name=_("Region"), max_length=255,
                              choices=AMAZON_REGIONS_CHOICES, default=EUROPE)

    def __str__(self):
        """Return Value."""
        return self.region + " - " + self.country.name + " - " + self.marketplaceId + " - " + self.region


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
