import os
import uuid

from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import HStoreField
from django.db import IntegrityError, models, router, transaction
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
from multiselectfield import MultiSelectField

from bat.autoemail.constants import (
    BUYER_PURCHASE_CHOICES,
    CHANNEL_CHOICES,
    DAILY,
    EMAIL_LANG_CHOICES,
    EMAIL_LANG_ENGLISH,
    EXCLUDE_ORDERS_CHOICES,
    PER_EMAIL_CHARGED_POINTS,
    PER_EMAIL_CHARGED_POINTS_FOR_INVOICE,
    SCHEDULE_CHOICES,
)
from bat.autoemail.utils import send_email
from bat.company.models import Company
from bat.globalutils.utils import pdf_file_from_html
from bat.market.models import AmazonMarketplace, AmazonOrder
from bat.setting.models import Status

try:
    from unidecode import unidecode
except ImportError:

    def unidecode(text):
        return text


User = get_user_model()
STATUS_DRAFT = 4


def template_logo_name(instance, filename):
    """Manage path and name for template logo."""
    name, extension = os.path.splitext(filename)
    return "company/email/{0}/{1}/{2}_{3}{4}".format(
        "template", "logo", str(name), uuid.uuid4(), extension
    )


def attachment_file_name(instance, filename):
    """Change name of attachment file."""
    name, extension = os.path.splitext(filename)
    return "company/email/{0}/{1}/{2}_{3}{4}".format(
        "template", "attachment", str(name), uuid.uuid4(), extension
    )


class GlobalEmailTemplate(models.Model):
    """Global Email Template for the auto email and will be set ad default."""

    name = models.CharField(verbose_name=_("Name"), max_length=512)
    subject = models.CharField(verbose_name=_("Subject"), max_length=512)
    default_cc = models.CharField(max_length=2096, null=True, blank=True)
    language = models.CharField(
        max_length=50,
        verbose_name=_("Language"),
        choices=EMAIL_LANG_CHOICES,
        default=EMAIL_LANG_ENGLISH,
    )
    template = models.TextField()
    slug = models.SlugField(unique=True)
    is_active = models.BooleanField(default=True)
    extra_data = HStoreField(null=True, blank=True)
    create_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        """Return Value."""
        return self.name


class GlobalEmailCampaign(models.Model):
    """Global Email Campaign for the auto email."""

    name = models.CharField(verbose_name=_("Name"), max_length=512)
    emailtemplate = models.ForeignKey(
        GlobalEmailTemplate, on_delete=models.CASCADE
    )
    status = models.ForeignKey(
        Status,
        on_delete=models.PROTECT,
        default=STATUS_DRAFT,
        related_name="globalemailcampaign_status",
    )
    amazonmarketplace = models.ForeignKey(
        AmazonMarketplace, on_delete=models.CASCADE
    )
    order_status = models.ForeignKey(
        Status,
        on_delete=models.PROTECT,
        default=STATUS_DRAFT,
        related_name="globalemailcampaign_order_status",
    )
    channel = MultiSelectField(
        max_length=50, verbose_name=_("Channel"), choices=CHANNEL_CHOICES
    )
    schedule = models.CharField(
        max_length=50,
        verbose_name=_("Schedule"),
        choices=SCHEDULE_CHOICES,
        default=DAILY,
    )
    schedule_time = models.TimeField(default=timezone.now)
    schedule_days = models.PositiveIntegerField(default=1)
    buyer_purchase_count = MultiSelectField(
        max_length=512,
        verbose_name=_("Buyer's Purchase Count"),
        choices=BUYER_PURCHASE_CHOICES,
        blank=True,
    )
    exclude_orders = MultiSelectField(
        max_length=512,
        verbose_name=_("Exclude Orders"),
        choices=EXCLUDE_ORDERS_CHOICES,
        blank=True,
    )
    include_invoice = models.BooleanField(default=False)
    extra_data = HStoreField(null=True, blank=True)
    create_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        """Return Value."""
        return self.name


class EmailTemplate(models.Model):
    """Email Template for the auto email."""

    name = models.CharField(verbose_name=_("Name"), max_length=512)
    subject = models.CharField(verbose_name=_("Subject"), max_length=512)
    default_cc = models.CharField(max_length=2096, null=True, blank=True)
    logo = models.ImageField(
        upload_to=template_logo_name, blank=True, verbose_name=_("Logo")
    )
    attachment_file = models.FileField(
        upload_to=attachment_file_name,
        blank=True,
        verbose_name=_("Attachment File"),
    )
    language = models.CharField(
        max_length=50,
        verbose_name=_("Language"),
        choices=EMAIL_LANG_CHOICES,
        default=EMAIL_LANG_ENGLISH,
    )
    template = models.TextField()
    slug = models.SlugField(unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    extra_data = HStoreField(null=True, blank=True)
    create_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        """Return Value."""
        return self.name

    def slugify(self, name, i=None):
        slug = slugify(unidecode(name))
        if i is not None:
            slug += "_%d" % i
        return slug

    def save(self, *args, **kwargs):
        if self._state.adding and not self.slug:
            self.slug = self.slugify(self.name)
            try:
                with transaction.atomic():
                    res = super().save(*args, **kwargs)
                return res
            except IntegrityError:
                pass
            # Now try to find existing slugs with similar names
            slugs = set(
                type(self)
                ._default_manager.filter(slug__startswith=self.slug)
                .values_list("slug", flat=True)
            )
            i = 1
            while True:
                slug = self.slugify(self.name, i)
                if slug not in slugs:
                    self.slug = slug
                    return super().save(*args, **kwargs)
                i += 1
        else:
            return super().save(*args, **kwargs)


class EmailCampaign(models.Model):
    """Email Campaign for the auto email."""

    name = models.CharField(verbose_name=_("Name"), max_length=512)
    emailtemplate = models.ForeignKey(EmailTemplate, on_delete=models.CASCADE)
    status = models.ForeignKey(
        Status,
        on_delete=models.PROTECT,
        default=STATUS_DRAFT,
        related_name="emailcampaign_status",
    )
    amazonmarketplace = models.ForeignKey(
        AmazonMarketplace, on_delete=models.CASCADE
    )
    order_status = models.ForeignKey(
        Status,
        on_delete=models.PROTECT,
        default=STATUS_DRAFT,
        related_name="emailcampaign_order_status",
    )
    channel = MultiSelectField(
        max_length=50, verbose_name=_("Channel"), choices=CHANNEL_CHOICES
    )
    schedule = models.CharField(
        max_length=50,
        verbose_name=_("Schedule"),
        choices=SCHEDULE_CHOICES,
        default=DAILY,
    )
    schedule_time = models.TimeField(default=timezone.now)
    schedule_days = models.PositiveIntegerField(default=1)
    buyer_purchase_count = MultiSelectField(
        max_length=512,
        verbose_name=_("Buyer's Purchase Count"),
        choices=BUYER_PURCHASE_CHOICES,
        blank=True,
    )
    exclude_orders = MultiSelectField(
        max_length=512,
        verbose_name=_("Exclude Orders"),
        choices=EXCLUDE_ORDERS_CHOICES,
        blank=True,
    )
    include_invoice = models.BooleanField(default=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    extra_data = HStoreField(null=True, blank=True)
    create_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        """Return Value."""
        return self.name

    def get_company(self):
        return self.emailtemplate.company

    def get_charged_points(self):

        points = PER_EMAIL_CHARGED_POINTS

        if self.include_invoice:
            points += PER_EMAIL_CHARGED_POINTS_FOR_INVOICE

        return points


class EmailQueue(models.Model):
    """Email Queue for the auto email."""

    amazonorder = models.ForeignKey(
        AmazonOrder, on_delete=models.CASCADE, verbose_name="Select Order"
    )
    emailcampaign = models.ForeignKey(EmailCampaign, on_delete=models.CASCADE)
    sent_to = models.CharField(verbose_name=_("Sent to Email"), max_length=512)
    sent_from = models.CharField(
        verbose_name=_("Sent from Email"), max_length=512
    )
    subject = models.CharField(verbose_name=_("Subject"), max_length=512)
    template = models.ForeignKey(EmailTemplate, on_delete=models.PROTECT)
    status = models.ForeignKey(
        Status, on_delete=models.PROTECT, related_name="email_queue"
    )
    send_date = models.DateTimeField(null=True, blank=True)
    schedule_date = models.DateTimeField(default=timezone.now)
    extra_data = HStoreField(null=True, blank=True)
    create_date = models.DateTimeField(default=timezone.now)
    update_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        """Return Value."""
        return self.subject + " - " + self.sent_to

    def get_company(self):
        return self.template.company

    def send_mail(self):
        products = self.amazonorder.orderitem_order.all()
        products_title_s = ""
        for product in products:
            products_title_s += product.amazonproduct.title + ", "
        context = {
            "order_id": self.amazonorder.order_id,
            "Product_title_s": products_title_s,
            "Seller_name": self.get_company().name,
        }
        if self.emailcampaign.include_invoice:
            f = self.generate_pdf_file()
            send_email(
                self.template,
                self.sent_to,
                context=context,
                attachment_files=[f],
            )
        else:
            send_email(self.template, self.sent_to, context=context)

    def generate_pdf_file(self):
        """
        generate pdf file
        """
        data = {
            "data": "I am order",
            "order_id": str(self.amazonorder.order_id),
            "purchase_date": str(self.amazonorder.purchase_date),
            "total_amount": str(self.amazonorder.amount),
            "tax": str(self.amazonorder.tax),
            "order_items": self.amazonorder.orderitem_order.all(),
            "seller_name": self.get_company().name,
        }
        name = "order_invoice_" + str(self.amazonorder.order_id)
        f = pdf_file_from_html(
            data, "autoemail/order_invoice.html", name, as_File_obj=False
        )
        return f
