"""Class to setup cronjob."""

from time import sleep

from bat.setting.models import AmazonMwsauth, MWSReports
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone
from mws import mws


class Command(BaseCommand):
    """Command to execute."""

    help = "TO fetch order from old server and store orders"

    def handle(self, *args, **options):
        """Submit MWS API reports to Amazon."""
        mwsreports = MWSReports.objects.filter(
            report_status="_PENDING_"
        ).order_by("-submitted_date")[:5]
        for mwsreport in mwsreports:
            print("Pending " + str(mwsreport.id))
            amazonmwsauth = AmazonMwsauth.objects.get(
                region=mwsreport.amazonmarket.region
            )
            try:
                reportsApi = mws.Reports(
                    access_key=amazonmwsauth.access_key,
                    secret_key=amazonmwsauth.secret_key,
                    account_id=amazonmwsauth.seller_id,
                    auth_token=amazonmwsauth.auth_token,
                    region=mwsreport.amazonmarket.name,
                )

                if mwsreport.start_date and mwsreport.end_date:
                    request_report = reportsApi.request_report(
                        report_type=mwsreport.report_type,
                        start_date=mwsreport.start_date,
                        end_date=mwsreport.end_date,
                    )
                elif mwsreport.start_date:
                    request_report = reportsApi.request_report(
                        report_type=mwsreport.report_type,
                        start_date=mwsreport.start_date,
                    )
                elif mwsreport.end_date:
                    request_report = reportsApi.request_report(
                        report_type=mwsreport.report_type,
                        end_date=mwsreport.end_date,
                    )
                else:
                    request_report = reportsApi.request_report(
                        report_type=mwsreport.report_type
                    )

                reportresponse = (
                    mws.utils.XML2Dict()
                    .fromstring(request_report.original)
                    .get("RequestReportResponse", {})
                )

                report_request_id = (
                    reportresponse.get("RequestReportResult")
                    .get("ReportRequestInfo")
                    .get("ReportRequestId")
                    .get("value")
                )
                start_date = (
                    reportresponse.get("RequestReportResult")
                    .get("ReportRequestInfo")
                    .get("StartDate")
                    .get("value")
                )
                end_date = (
                    reportresponse.get("RequestReportResult")
                    .get("ReportRequestInfo")
                    .get("EndDate")
                    .get("value")
                )
                submitted_date = (
                    reportresponse.get("RequestReportResult")
                    .get("ReportRequestInfo")
                    .get("SubmittedDate")
                    .get("value")
                )
                status = (
                    reportresponse.get("RequestReportResult")
                    .get("ReportRequestInfo")
                    .get("ReportProcessingStatus")
                    .get("value")
                )
                request_id = (
                    reportresponse.get("ResponseMetadata")
                    .get("RequestId")
                    .get("value")
                )

                mwsreport.report_status = status
                mwsreport.start_date = start_date
                mwsreport.end_date = end_date
                mwsreport.report_request_id = report_request_id
                mwsreport.submitted_date = submitted_date
                mwsreport.request_id = request_id
                mwsreport.save()

                sleep(20)
            except mws.MWSError:
                mwsreport.report_status = "_CREDENTAIL_ERROR_"
                mwsreport.save()
        # Amazon report request List.
        mwsreports = MWSReports.objects.filter(
            Q(report_status="_SUBMITTED_") | Q(report_status="_IN_PROGRESS_")
        ).order_by("-submitted_date")[:5]
        for mwsreport in mwsreports:
            print("Submitted " + str(mwsreport.id))
            amazonmwsauth = AmazonMwsauth.objects.get(
                region=mwsreport.amazonmarket.region
            )
            try:
                reportsApi = mws.Reports(
                    access_key=amazonmwsauth.access_key,
                    secret_key=amazonmwsauth.secret_key,
                    account_id=amazonmwsauth.seller_id,
                    auth_token=amazonmwsauth.auth_token,
                    region=mwsreport.amazonmarket.name,
                )

                request_report_list = reportsApi.get_report_request_list(
                    requestids=[mwsreport.report_request_id]
                )
                report_status = (
                    mws.utils.XML2Dict()
                    .fromstring(request_report_list.original)
                    .get("GetReportRequestListResponse", {})
                    .get("GetReportRequestListResult")
                    .get("ReportRequestInfo")
                    .get("ReportProcessingStatus")
                    .get("value")
                )
                print(report_status)
                if report_status == "_DONE_":
                    report_id = (
                        mws.utils.XML2Dict()
                        .fromstring(request_report_list.original)
                        .get("GetReportRequestListResponse", {})
                        .get("GetReportRequestListResult")
                        .get("ReportRequestInfo")
                        .get("GeneratedReportId")
                        .get("value")
                    )
                    mwsreport.report_status = report_status
                    mwsreport.report_id = report_id
                    mwsreport.save()
                else:
                    mwsreport.report_status = report_status
                    mwsreport.save()

                sleep(20)
            except mws.MWSError:
                mwsreport.report_status = "_CREDENTAIL_ERROR_"
                mwsreport.save()

        self.stdout.write(
            self.style.SUCCESS("Sync Amazon data " + str(timezone.now()))
        )
