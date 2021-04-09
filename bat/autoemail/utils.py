from bat.mailsender.senders import EmailNotificationSender
# from bat.autoemail.models import EmailTemplate


def send_email(template, recipients, cc=[], bcc=[], context={}, subject=None, attachment_files=[]):
    # template = EmailTemplate.objects.get(slug=template_slug)
    sender = EmailNotificationSender(template, recipients, cc=cc,
                                     bcc=bcc, context=context, subject=subject, attachment_files=attachment_files)
    return sender.send()
