"""Task that can run by celery will be placed here."""
import csv
import time
import tempfile
from celery.utils.log import get_task_logger
from config.celery import app
from datetime import datetime, timedelta

from django.conf import settings

from sp_api.base import Marketplaces
from sp_api.base.reportTypes import ReportType
from bat.market.amazon_sp_api.amazon_sp_api import Reports

from bat.market.models import (
    AmazonAccounts,
    AmazonProduct,
    AmazonOrder,
)
from bat.market.report_parser import (ReportAmazonProductCSVParser, ReportAmazonOrdersCSVParser,)
from bat.market.utils import get_amazon_report

logger = get_task_logger(__name__)


@app.task
def amazon_products_sync_account(amazonaccount_id):
    amazonaccount = AmazonAccounts.objects.get(pk=amazonaccount_id)
    logger.info("celery amazon_products_sync_account task")

    # Temporary files
    tmp_dir = tempfile.TemporaryDirectory()
    timestamp = datetime.timestamp(datetime.now())
    tmp_csv_file_path = tmp_dir.name + "/product_report" + str(timestamp) + ".csv"

    report_file = open(tmp_csv_file_path, "w+")

    start_time = (datetime.utcnow() - timedelta(days=60)).isoformat()
    end_time = (datetime.utcnow()).isoformat()

    # get report data (report api call)
    get_amazon_report(amazonaccount, ReportType.GET_MERCHANT_LISTINGS_ALL_DATA,
                      report_file, start_time, end_time)

    # read report data from files
    report_csv = open(tmp_csv_file_path, "r")

    # process data for import
    data, columns = ReportAmazonProductCSVParser.parse(report_csv)

    # import formated data
    AmazonProduct.objects.import_bulk(data, amazonaccount, columns)


@app.task
def amazon_products_sync():
    """fetch product data from amazon account and sync system product data with that."""
    logger.info("amazon_products_sync task")
    for account in AmazonAccounts.objects.all():
        amazon_products_sync_account.apply_async([account.id])


@app.task
def amazon_orders_sync_account(amazonaccount_id, last_no_of_days=1):
    amazonaccount = AmazonAccounts.objects.get(pk=amazonaccount_id)
    logger.info("celery amazon_orders_sync_account task")

    # Temporary files
    timestamp = datetime.timestamp(datetime.now())
    tmp_dir = tempfile.TemporaryDirectory()
    tmp_orders_csv_file_path = tmp_dir.name + "/orders_report" + str(timestamp) + ".csv"
    tmp_items_csv_file_path = tmp_dir.name + "/items_report" + str(timestamp) + ".csv"

    orders_report_file = open(tmp_orders_csv_file_path, "w+")
    orders_items_report_file = open(tmp_items_csv_file_path, "w+")

    start_time = (datetime.utcnow() - timedelta(days=last_no_of_days)).isoformat()
    end_time = (datetime.utcnow()).isoformat()

    # get report data (report api call)
    get_amazon_report(amazonaccount, ReportType.GET_FLAT_FILE_ALL_ORDERS_DATA_BY_ORDER_DATE_GENERAL,
                      orders_report_file, start_time, end_time)
    get_amazon_report(amazonaccount, ReportType.GET_AMAZON_FULFILLED_SHIPMENTS_DATA_GENERAL,
                      orders_items_report_file, start_time, end_time)

    # read report data from files
    orders_report_csv = open(tmp_orders_csv_file_path, "r")
    orders_items_report_csv = open(tmp_items_csv_file_path, "r")

    # process data for import
    data, order_columns, item_columns = ReportAmazonOrdersCSVParser.parse(
        orders_report_csv, orders_items_report_csv)

    # import formated data
    AmazonOrder.objects.import_bulk(
        data, amazonaccount, order_columns, item_columns)


@app.task
def amazon_orders_sync():
    """fetch orders data from amazon account and sync system orders data with that."""
    logger.info("amazon_orders_sync task")
    for account in AmazonAccounts.objects.all():
        amazon_orders_sync_account.apply_async([account.id])


@app.task
def amazon_account_products_orders_sync(amazonaccount_id, last_no_of_days=1):
    logger.info("amazon_account_products_orders_sync task")
    amazon_products_sync_account.apply_async(
        [amazonaccount_id], callback=amazon_orders_sync_account.s(amazonaccount_id, last_no_of_days))
