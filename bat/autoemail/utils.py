from bat.mailsender.senders import EmailNotificationSender
from bat.autoemail.models import EmailTemplate


def send_email(template_slug, recipients, cc=[], bcc=[], context={}, subject=None):
    template = EmailTemplate.objects.get(slug=template_slug)
    sender = EmailNotificationSender(template, recipients, cc=cc,
                                     bcc=bcc, context=context, subject=subject)
    return sender.send()


