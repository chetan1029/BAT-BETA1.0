from django_filters.rest_framework import filters, filterset

from bat.product.constants import PRODUCT_PARENT_STATUS
from bat.product.models import Product


class ProductFilter(filterset.FilterSet):
    """
    provide filter set to products
    """

    tags = filters.CharFilter(field_name="tags", method="filter_by_tags")
    status = filters.CharFilter(field_name="status", method="filter_by_status")

    def filter_by_tags(self, qs, name, value):
        tag_list = value.split(",")
        return qs.filter(tags__name__in=tag_list).distinct()

    def filter_by_status(self, qs, name, value):
        return qs.filter(
            status__name__iexact=value,
            status__parent__name=PRODUCT_PARENT_STATUS,
        ).distinct()

    class Meta:
        model = Product
        fields = ["is_component", "type"]
