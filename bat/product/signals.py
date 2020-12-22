from django.db.models.signals import post_save
from django.dispatch import receiver

from bat.product.models import ProductParent
from bat.company.models import ComponentMe
from bat.product.constants import PRODUCT_PARENT_STATUS, PRODUCT_STATUS_DISCONTINUED, PRODUCT_STATUS_ARCHIVE
from bat.setting.utils import get_status


@receiver(post_save, sender=ProductParent)
def archive_component_me_on_discontinued(sender, instance, **kwargs):
    if instance.status == get_status(PRODUCT_PARENT_STATUS, PRODUCT_STATUS_DISCONTINUED):
        products_ids = list(instance.products.values_list("id", flat=True))
        component_mes = ComponentMe.objects.filter(component__in=products_ids)
        component_mes.update(is_active=False)
        archive_status = get_status(
            PRODUCT_PARENT_STATUS, PRODUCT_STATUS_ARCHIVE)
        component_mes.update(status=archive_status)
