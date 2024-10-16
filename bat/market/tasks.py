"""Task that can run by celery will be placed here."""
import tempfile

from celery.utils.log import get_task_logger
from config.celery import app
from datetime import datetime, timedelta

from sp_api.base.reportTypes import ReportType

from bat.market.models import (
    AmazonAccounts,
    AmazonProduct,
    AmazonOrder,
)
from bat.market.report_parser import (ReportAmazonProductCSVParser, ReportAmazonOrdersCSVParser,)
from bat.market.utils import get_amazon_report
from bat.autoemail.tasks import email_queue_create_for_orders, email_queue_create_for_initial_orders

logger = get_task_logger(__name__)


@app.task
def amazon_account_products_orders_sync(amazonaccount_id, last_no_of_days=1, is_orders_sync=True):
    logger.info("Amazon Product "+str(amazonaccount_id))
    amazonaccount = AmazonAccounts.objects.get(pk=amazonaccount_id)
    logger.info("celery amazon_account_products_orders_sync task")

    # Temporary files
    timestamp = datetime.timestamp(datetime.now())
    tmp_dir = tempfile.TemporaryDirectory()
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

    if is_orders_sync:
        amazon_orders_sync_account.apply_async([amazonaccount.id, last_no_of_days])


@app.task
def amazon_products_orders_sync(last_no_of_days=1):
    """fetch products data and orders data from amazon account and sync system products and orders data with that."""
    logger.info("amazon_products_sync task")
    for account in AmazonAccounts.objects.all():
        amazon_account_products_orders_sync.apply_async([account.id, last_no_of_days])


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
        orders_report_csv, orders_items_report_csv, amazonaccount)

    # import formated data
    amazon_created_orders_pk, amazon_updated_orders_pk, amazon_orders_old_status_map = AmazonOrder.objects.import_bulk(
        data, amazonaccount, order_columns, item_columns)

    # auto campaign
    if last_no_of_days == 1:
        email_queue_create_for_orders.delay(
            amazonaccount_id, amazon_created_orders_pk, amazon_updated_orders_pk, amazon_orders_old_status_map)
    else:
        email_queue_create_for_initial_orders.delay(
            amazonaccount_id, amazon_created_orders_pk)


@app.task
def amazon_orders_sync():
    """fetch orders data from amazon account and sync system orders data with that."""
    logger.info("amazon_orders_sync task")
    for account in AmazonAccounts.objects.all():
        amazon_orders_sync_account.apply_async([account.id])


@app.task
def amazon_products_sync():
    """fetch product data from amazon account and sync system products data with that."""
    logger.info("amazon_products_sync task")
    for account in AmazonAccounts.objects.all():
        amazon_account_products_orders_sync.apply_async(
            [account.id], kwargs={"is_orders_sync": False})
