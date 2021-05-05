import boto3
import botocore
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from rest_framework import status
from rest_framework.response import Response


def verify_ses_email(email):
    ses_connection = boto3.client("sesv2")
    try:
        verify_email = ses_connection.create_email_identity(
            EmailIdentity=email
        )
    except ses_connection.exceptions.AlreadyExistsException:
        return Response(
            {"detail": _("Email already exists.")},
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


def verify_ses_email_custom_template(email, template_name):
    ses_connection = boto3.client("sesv2")
    try:
        verify_email = ses_connection.send_custom_verification_email(
            EmailAddress=email, TemplateName=template_name
        )
    except ses_connection.exceptions.MailFromDomainNotVerifiedException:
        return Response(
            {"detail": _("Sending Email address not verified.")},
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
    except ses_connection.exceptions.NotFoundException:
        return Response(
            {"detail": _("Template doesn't exists on SES Email templates.")},
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


def verified_email_list():
    ses_connection = boto3.client("sesv2")
    email_list = ses_connection.list_email_identities(PageSize=1000)
    return email_list


def is_ses_email_verified(email):
    ses_connection = boto3.client("sesv2")
    verified = False
    try:
        email_identity = ses_connection.get_email_identity(EmailIdentity=email)
        verified = email_identity["VerifiedForSendingStatus"]
    except ses_connection.exceptions.NotFoundException:
        return False
    return verified


def create_verification_email_template(
    template_name,
    from_email,
    subject,
    content,
    success_redirect,
    error_redirect,
):
    ses_connection = boto3.client("sesv2")
    try:
        response = ses_connection.create_custom_verification_email_template(
            TemplateName=template_name,
            FromEmailAddress=from_email,
            TemplateSubject=subject,
            TemplateContent=content,
            SuccessRedirectionURL=success_redirect,
            FailureRedirectionURL=error_redirect,
        )
    except ses_connection.exceptions.AlreadyExistsException:
        response = ses_connection.update_custom_verification_email_template(
            TemplateName=template_name,
            FromEmailAddress=from_email,
            TemplateSubject=subject,
            TemplateContent=content,
            SuccessRedirectionURL=success_redirect,
            FailureRedirectionURL=error_redirect,
        )
    return ""
