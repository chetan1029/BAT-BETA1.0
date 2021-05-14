from django.contrib.postgres.fields import HStoreField
from django.db import models
from django.utils import timezone

from bat.keywordtracking.constants import KEYWORD_STATUS_ACTIVE
from bat.market.models import AmazonMarketplace, AmazonProduct
from bat.setting.models import Status


# Create your models here.
class Keyword(models.Model):
    """Search Keywords."""

    amazonmarketplace = models.ForeignKey(
        AmazonMarketplace, on_delete=models.CASCADE
    )
    name = models.CharField(max_length=512)
    frequency = models.PositiveIntegerField(default=0)
    create_date = models.DateTimeField(default=timezone.now)

    class Meta:
        """Keywords Meta."""

        unique_together = ("amazonmarketplace", "name")

    def __str__(self):
        """Return Value."""
        return str(self.name) + " - " + str(self.amazonmarketplace.country)


class ProductKeyword(models.Model):
    """Product Keywords."""

    amazonproduct = models.ForeignKey(
        AmazonProduct,
        on_delete=models.CASCADE,
        verbose_name="Select Amazon Product",
    )
    keyword = models.ForeignKey(
        Keyword, on_delete=models.CASCADE, verbose_name="Select Keyword"
    )
    status = models.ForeignKey(
        Status, on_delete=models.PROTECT
    )
    create_date = models.DateField(default=timezone.now)

    class Meta:
        """Product Keyword Meta."""

        unique_together = ("amazonproduct", "keyword")

    def __str__(self):
        """Return Value."""
        return str(self.amazonproduct.asin) + " - " + str(self.keyword.name)


class ProductKeywordRank(models.Model):
    """Keyword rank for amazon product."""

    productkeyword = models.ForeignKey(
        ProductKeyword,
        on_delete=models.CASCADE,
        verbose_name="Select Product Keyword",
    )
    index = models.BooleanField(default=False)
    rank = models.PositiveIntegerField(default=0)
    page = models.PositiveIntegerField(default=0)
    frequency = models.PositiveIntegerField(default=0)
    visibility_score = models.DecimalField(
        max_digits=5, decimal_places=2, default="0.0"
    )
    date = models.DateField(default=timezone.now)
    scrap_status = models.PositiveIntegerField(default=0)
    extra_data = HStoreField(null=True, blank=True)

    class Meta:
        """Product Keyword Meta."""

        unique_together = ("productkeyword", "date")

    def __str__(self):
        """Return Value."""
        return (
            str(self.productkeyword.keyword.name)
            + " - "
            + str(self.productkeyword.amazonproduct.asin)
            + " - Rank: "
            + str(self.rank)
            + " - Date: "
            + str(self.date)
        )
