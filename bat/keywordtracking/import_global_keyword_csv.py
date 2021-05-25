import csv
from io import StringIO

from django import forms
from django.utils import timezone

from bat.keywordtracking.models import GlobalKeyword


class CsvImportForm(forms.Form):
    csv_file = forms.FileField()


def import_global_keyword_csv(csv_file):
    def _clean(csv_file):
        decoded_file = csv_file.read().decode("utf-8").splitlines()
        decoded_file.pop(0)
        csv_reader = csv.DictReader(decoded_file, delimiter=",")
        headers = csv_reader.fieldnames
        data = []
        department = None
        for row in csv_reader:
            r = row.copy()
            for key, value in row.items():
                if department is None:
                    if key == "Department":
                        department = value
                if key == "Search Frequency Rank":
                    r[key] = value.replace(",", "")
            if r["Search Term"] != "" and r["Search Term"] != None:
                data.append(r)
        csvfile = StringIO()
        dict_writer = csv.DictWriter(csvfile, headers, extrasaction="ignore")
        dict_writer.writeheader()
        dict_writer.writerows(data)
        csvfile.seek(0)

        # delete
        if department is not None:
            GlobalKeyword.objects.filter(department=department).delete()

        return csvfile

    cleaned_csv_file = _clean(csv_file)
    GlobalKeyword.objects.from_csv(
        cleaned_csv_file,
        mapping=dict(
            department="Department",
            name="Search Term",
            frequency="Search Frequency Rank",
            asin_1="#1 Clicked ASIN",
            asin_2="#2 Clicked ASIN",
            asin_3="#3 Clicked ASIN",
        ),
        static_mapping={"create_date": timezone.now().isoformat()},
        drop_indexes=False,
        drop_constraints=False,
    )
