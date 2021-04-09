from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.contrib.auth import get_user_model
from django import template as djtemplate
from django.template import Context


User = get_user_model()


def send_mail(subject, message, from_email, recipient_list,
              fail_silently=False, auth_user=None, auth_password=None,
              connection=None, html_message=None, attachment_files=[]):
    """
    Easy wrapper for sending a single message to a recipient list. All members
    of the recipient list will see the other recipients in the 'To' field.

    If from_email is None, use the DEFAULT_FROM_EMAIL setting.
    If auth_user is None, use the EMAIL_HOST_USER setting.
    If auth_password is None, use the EMAIL_HOST_PASSWORD setting.

    Note: The API for this method is frozen. New code wanting to extend the
    functionality should use the EmailMessage class directly.
    """
    connection = connection or get_connection(
        username=auth_user,
        password=auth_password,
        fail_silently=fail_silently,
    )
    mail = EmailMultiAlternatives(subject, message, from_email,
                                  recipient_list, connection=connection)

    if attachment_files:
        for attachment_file in attachment_files:
            mail.attach(attachment_file.name, attachment_file.read())
            # mail.attach_file(attachment_file)

    if html_message:
        mail.attach_alternative(html_message, 'text/html')

    return mail.send()


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
        self._attachment_files = kwargs.pop("attachment_files")

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
            fail_silently=False,
            attachment_files=self._attachment_files
        )
