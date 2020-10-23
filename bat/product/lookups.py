"""Define lookup for the models to search."""
from __future__ import unicode_literals

import logging

from bat.company.models import HsCode
from bat.product.models import Product, ProductParent
from selectable.base import LookupBase, ModelLookup
from selectable.decorators import login_required
from selectable.registry import registry
from taggit.models import Tag

logger = logging.getLogger(__name__)


@login_required
class ProductTypeLookup(ModelLookup):
    """Product Type Lookup class."""

    model = ProductParent
    search_fields = ("type__icontains",)

    def get_query(self, request, term):
        """Modify get_query."""
        results = super(ProductTypeLookup, self).get_query(request, term)
        results = results.filter(
            company_id=request.member.company_id
        ).distinct("type")
        return results

    def get_item_value(self, item):
        """Display for currently selected item."""
        return item.type

    def get_item_label(self, item):
        """Display for choice listings."""
        return "%s" % (item.type)


registry.register(ProductTypeLookup)


@login_required
class ProductSeriesLookup(ModelLookup):
    """Product Series Lookup class."""

    model = ProductParent
    search_fields = ("series__icontains",)

    def get_query(self, request, term):
        """Modify get_query."""
        results = super(ProductSeriesLookup, self).get_query(request, term)
        results = results.filter(
            company_id=request.member.company_id
        ).distinct("series")
        return results

    def get_item_value(self, item):
        """Display for currently selected item."""
        return item.series

    def get_item_label(self, item):
        """Display for choice listings."""
        return "%s" % (item.series)


registry.register(ProductSeriesLookup)


@login_required
class ProductHsCodeLookup(ModelLookup):
    """Product HsCode Lookup class."""

    model = HsCode
    search_fields = ("hscode__icontains",)

    def get_query(self, request, term):
        """Modify get_query."""
        results = super(ProductHsCodeLookup, self).get_query(request, term)
        results = results.filter(
            company_id=request.member.company_id
        ).distinct("hscode")
        return results

    def get_item_value(self, item):
        """Display for currently selected item."""
        return item.hscode

    def get_item_label(self, item):
        """Display for choice listings."""
        return "%s (%s)" % (item.hscode, item.use)


registry.register(ProductHsCodeLookup)


@login_required
class ProductTagLookup(ModelLookup):
    """Product Tag Lookup class."""

    model = Tag
    search_fields = ("name__icontains",)

    def get_query(self, request, term):
        """Modify get_query."""
        results = super(ProductTagLookup, self).get_query(request, term)
        return results

    def get_item(self, value):
        """Display for choice listings."""
        return value

    def get_item_id(self, item):
        """Display for choice listings."""
        return item.name

    def get_item_label(self, item):
        """Display for choice listings."""
        return item.name


registry.register(ProductTagLookup)


class ProductOptionLookup(LookupBase):
    """Custom Lookup for product option."""

    def get_query(self, request, term):
        """Make a get_query."""
        data = ["Size", "Color", "Material", "Style"]
        return [x for x in data if x.startswith(term)]


registry.register(ProductOptionLookup)
