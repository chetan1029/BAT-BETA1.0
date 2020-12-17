from django_filters.rest_framework import filters, filterset

from bat.product.models import ProductParent


class ProductFilter(filterset.FilterSet):
    """
    provide filter set to products
    """
    tags = filters.CharFilter(field_name="tags", method='filter_by_tags')

    def filter_by_tags(self, qs, name, value):
        tag_list = value.split(",")
        return qs.filter(tags__name__in=tag_list).distinct()

    class Meta:
        model = ProductParent
        fields = ["is_active", "is_component", "type"]
