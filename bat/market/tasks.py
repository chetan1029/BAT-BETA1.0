"""Task that can run by celery will be placed here."""
import csv
import time
import tempfile
from celery.utils.log import get_task_logger
from config.celery import app
from datetime import datetime

from django.conf import settings

from sp_api.base import Marketplaces
from sp_api.base.reportTypes import ReportType
from bat.market.amazon_sp_api.amazon_sp_api import Reports

from bat.market.models import (
    AmazonAccounts,
    AmazonProduct,
)
from bat.market.report_parser import ReportAmazonProductCSVParser
from bat.market.constants import MARKETPLACE_CODES

logger = get_task_logger(__name__)


@app.task
def amazon_products_sync_account(amazonaccount_id):
    amazonaccount = AmazonAccounts.objects.get(pk=amazonaccount_id)
    logger.info("celery amazon_products_sync_account task")
    credentails = amazonaccount.credentails
    marketplace = amazonaccount.marketplace
    response_1 = Reports(
        marketplace=Marketplaces[MARKETPLACE_CODES.get(marketplace.marketplaceId)],
        refresh_token=credentails.refresh_token,
        credentials={
            "refresh_token": credentails.refresh_token,
            "lwa_app_id": settings.LWA_CLIENT_ID,
            "lwa_client_secret": settings.LWA_CLIENT_SECRET,
            "aws_access_key": settings.AWS_ACCESS_KEY_ID,
            "aws_secret_key": settings.AWS_SECRET_ACCESS_KEY,
            "role_arn": settings.ROLE_ARN,
        }
    ).create_report(reportType=ReportType.GET_MERCHANT_LISTINGS_ALL_DATA,
                    dataStartTime='2019-12-10T20:11:24.000Z',
                    marketplaceIds=[
                        marketplace.marketplaceId
                    ])

    reportId = int(response_1.payload["reportId"])

    iteration = 1
    response_2_payload = {}
    while response_2_payload.get("processingStatus", None) != "DONE":
        response_2 = Reports(
            marketplace=Marketplaces.US,
            refresh_token=credentails.refresh_token,
            credentials={
                "refresh_token": credentails.refresh_token,
                "lwa_app_id": settings.LWA_CLIENT_ID,
                "lwa_client_secret": settings.LWA_CLIENT_SECRET,
                "aws_access_key": settings.AWS_ACCESS_KEY_ID,
                "aws_secret_key": settings.AWS_SECRET_ACCESS_KEY,
                "role_arn": settings.ROLE_ARN,
            }
        ).get_report(reportId)
        response_2_payload = response_2.payload
        if response_2_payload.get("processingStatus", None) != "DONE":
            time.sleep(10)
        iteration = iteration + 1
        if(iteration > 10):
            break

    # Temporary files
    tmp_dir = tempfile.TemporaryDirectory()
    timestamp = datetime.timestamp(datetime.now())
    tmp_csv_file_path = tmp_dir.name + "/product_report" + str(timestamp) + ".csv"

    report_file = open(tmp_csv_file_path, "w+")

    data = Reports(
        marketplace=Marketplaces.US,
        refresh_token=credentails.refresh_token,
        credentials={
            "refresh_token": credentails.refresh_token,
            "lwa_app_id": settings.LWA_CLIENT_ID,
            "lwa_client_secret": settings.LWA_CLIENT_SECRET,
            "aws_access_key": settings.AWS_ACCESS_KEY_ID,
            "aws_secret_key": settings.AWS_SECRET_ACCESS_KEY,
            "role_arn": settings.ROLE_ARN,
        },
    ).get_report_document(response_2_payload["reportDocumentId"], decrypt=True, file=report_file)

    report_csv = open(tmp_csv_file_path, "r")
    data, columns = ReportAmazonProductCSVParser.parse(report_csv)
    AmazonProduct.objects.import_bulk(data, amazonaccount, columns)


@app.task
def amazon_products_sync():
    """Demo task."""
    logger.info("amazon_products_sync task")
    for account in AmazonAccounts.objects.all():
        amazon_products_sync_account.apply_async([account.id])
