import tempfile
import json
from decimal import Decimal


from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse


from rest_framework import status

from taggit.models import Tag, TaggedItem
import openpyxl
from measurement.measures import Weight

from bat.setting.utils import get_status
from bat.product.constants import (
    PRODUCT_PARENT_STATUS,
    PRODUCT_STATUS
)
from bat.company.models import HsCode
from bat.product.models import Product


def import_products_bulk_excel(company, import_file):
    # get model_number map with map
    products_map_tuple = Product.objects.filter(
        company_id=company.id).values_list("model_number", "id")
    products_map = {k: v for k, v in products_map_tuple}

    # get exsisting hscoad map
    hscode_map_tuple = HsCode.objects.filter(company_id=company.id).values_list("hscode", "id")
    hscode_map = {k: v for k, v in hscode_map_tuple}

    # read file
    ws = openpyxl.load_workbook(import_file)
    sheet = ws.active

    # get column's list
    header = [cell.value for cell in sheet[1]]
    header = header[1:]

    # add column for errors
    lat_col_index = len(header)+2
    header_cell = sheet.cell(row=1, column=lat_col_index)
    header_cell.value = "errors"
    header.append(header_cell.value)

    # get exsisting tags map
    tags_map = {}
    if "tags" in header:
        tags_map_tuple = Tag.objects.all().values_list("name", "id")
        tags_map = {k: v for k, v in tags_map_tuple}

    # create model objects
    product_tags_map = {}
    tag_objs = []
    products_id = []
    products_update = []
    hscode_objs = []
    for row in sheet.iter_rows(min_row=2, min_col=2):
        values = {}
        # process each value
        for key, cell in zip(header, row):
            if key == "status":
                values[key] = get_status(PRODUCT_PARENT_STATUS, PRODUCT_STATUS.get(
                    cell.value.lower())) if cell.value else None
            elif key == "weight":
                value = cell.value.replace(" g", "") if cell.value else None
                value = Weight({"g": Decimal(value)})
                values[key] = value
            elif key == "tags":
                values[key] = cell.value.split(",") if cell.value else None
                ct = ContentType.objects.get(app_label='product', model='product')
            elif key == "hscode":
                try:
                    _hscode_id = hscode_map.get(cell.value)
                    values[key] = cell.value if cell.value else ""
                except KeyError as e:
                    hscode_objs.append(HsCode(company=company, hscode=cell.value))
            elif key in ["bullet_points", "description"]:
                values[key] = cell.value if cell.value else ""
            elif key == "errors":
                pass
            else:
                values[key] = cell.value

        # process on product object
        try:
            product_id = products_map[values.get("model_number", None)]
            products_id.append(product_id)
            if "tags" in header:
                tags = values.pop("tags", None)
                if not tags is None:
                    product_tags_map[product_id] = tags
                    for tag in tags:
                        try:
                            _t = tags_map[tag]
                        except KeyError as e:
                            tag_objs.append(Tag(name=tag, slug=tag))

            product = Product(id=product_id, company=company, **values)
            try:
                # validate object
                product.full_clean(exclude=["id"])
                products_update.append(product)
            except ValidationError as e:
                # add validation error in file
                error_cell = sheet.cell(row=row[0].row, column=lat_col_index)
                error_cell.value = json.dumps(e.message_dict)
        except KeyError as e:
            print("have to create object")

    # create temporaryfile
    tmp_dir = tempfile.TemporaryDirectory()
    tmp_xlsx_file_path = tmp_dir.name + "/" + import_file.name

    # save changes in uploaded file
    ws.save(tmp_xlsx_file_path)
    ws.close()

    # open saved file
    ext = import_file.name.split(".")[-1]
    f = open(tmp_xlsx_file_path, "rb")

    response_args = {'content_type': 'application/'+ext}
    response = HttpResponse(f, **response_args)
    response['Content-Disposition'] = 'attachment; filename=' + \
        import_file.name

    response['Cache-Control'] = 'no-cache'
    try:
        # perform bulk operations
        with transaction.atomic():

            HsCode.objects.bulk_create(hscode_objs)

            header2 = header.copy()
            header2.remove("tags")
            Product.objects.bulk_update(products_update, header2[:-1])

            if "tags" in header:
                # delete exsisting tagitems
                ct = ContentType.objects.get(app_label='product', model='product')

                TaggedItem.objects.filter(
                    content_type_id=ct.id, object_id__in=products_id).delete()

                # create new objects
                Tag.objects.bulk_create(tag_objs)

                # create tagitems objects
                #   > get exsisting tags map
                tags_map2 = {}
                if "tags" in header:
                    tags_map_tuple2 = Tag.objects.all().values_list("name", "id")
                    tags_map2 = {k: v for k, v in tags_map_tuple2}

                #   > tagitem objects
                tag_item_objs = []
                for product_id, tags in product_tags_map.items():
                    for tag in tags:
                        tag_item_objs.append(TaggedItem(tag_id=tags_map2.get(
                            tag), object_id=product_id, content_type_id=ct.id))
                TaggedItem.objects.bulk_create(tag_item_objs)

    except Exception as e:
        response_args["status"] = status.HTTP_500_INTERNAL_SERVER_ERROR

    # send file in response
    return response
