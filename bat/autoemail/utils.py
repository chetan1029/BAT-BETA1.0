from bat.mailsender.boto_ses import is_ses_email_verified
from bat.mailsender.senders import EmailNotificationSender

# from bat.autoemail.models import EmailTemplate


def send_email(
    template,
    recipients,
    sent_from,
    cc=[],
    bcc=[],
    context={},
    subject=None,
    attachment_files=[],
):
    # template = EmailTemplate.objects.get(slug=template_slug)
    sender = EmailNotificationSender(
        template,
        recipients,
        sent_from,
        cc=cc,
        bcc=bcc,
        context=context,
        subject=subject,
        attachment_files=attachment_files,
    )
    return sender.send()


def update_ses_email_verification(account_credentails):
    if account_credentails.email and not account_credentails.email_verified:
        status = is_ses_email_verified(account_credentails.email)
        account_credentails.email_verified = status
        account_credentails.save()
