from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from django import template as djtemplate
from django.template import Context


User = get_user_model()


class MessageParser(object):
    def get_message(self, template, context):
        tpl = djtemplate.Template(template.template)
        return tpl.render(Context(context))


class EmailNotificationSender(MessageParser):
    """
    handle sending email notifications.
    """

    def __init__(self, template, recipients, *args, **kwargs):
        self._kwargs = kwargs
        self._template = template
        self._recipient_list = self._get_recipient_list(recipients)
        self._cc = kwargs.pop('cc', None)
        self._bcc = kwargs.pop('bcc', None)
        self._user = kwargs.pop('user', None)
        self._context = kwargs.get("context")
        self._subject = self._get_subject()
        self._message = self.get_message(self._template, self._context)
        self._from_email = self._get_from_email()

    def _get_from_email(self):
        return settings.MAIL_FROM_ADDRESS

    def _get_recipient_list(self, recipients):

        if not isinstance(recipients, list) and isinstance(recipients, User):
            return [recipients.email]
        elif isinstance(recipients, str):
            return [recipients]
        else:
            emails = []
            for recipient in recipients:
                if isinstance(recipient, User):
                    emails.append(recipient.email)
            return emails

    def _get_subject(self):
        subject = self._kwargs.get("subject") if self._kwargs.get(
            "subject") is not None else self._template.subject
        tpl = djtemplate.Template(subject)
        return tpl.render(Context(self._context))

    def send(self):
        msg = send_mail(
            self._subject,
            self._message,
            self._from_email,
            self._recipient_list,
            fail_silently=False
        )
