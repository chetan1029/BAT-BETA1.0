import csv
from io import StringIO

from django import forms
from django.contrib import admin
from django.shortcuts import redirect, render
from django.urls import path
from django.utils import timezone

from bat.keywordtracking.models import (
    GlobalKeyword,
    Keyword,
    ProductKeyword,
    ProductKeywordRank,
)

admin.site.register(Keyword)
admin.site.register(ProductKeyword)
admin.site.register(ProductKeywordRank)


class CsvImportForm(forms.Form):
    csv_file = forms.FileField()


@admin.register(GlobalKeyword)
class HeroAdmin(admin.ModelAdmin):
    change_list_template = "keywordtracking/globalkeywords_changelist.html"

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [path("import-csv/", self.import_csv)]
        return my_urls + urls

    def import_csv(self, request):
        def _clean(csv_file):
            decoded_file = csv_file.read().decode("utf-8").splitlines()
            reader = csv.DictReader(decoded_file, delimiter=",")
            headers = reader.fieldnames
            data = []
            for row in reader:
                r = row.copy()
                for key, value in row.items():
                    if key == "Search Frequency Rank":
                        r[key] = value.replace(",", "")
                data.append(r)
            csvfile = StringIO()
            dict_writer = csv.DictWriter(
                csvfile, headers, extrasaction="ignore"
            )
            dict_writer.writeheader()
            dict_writer.writerows(data)
            csvfile.seek(0)
            return csvfile

        if request.method == "POST":
            csv_file1 = request.FILES["csv_file"]
            csv_file = _clean(csv_file1)

            GlobalKeyword.objects.from_csv(
                csv_file,
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
            return redirect("..")
        form = CsvImportForm()
        payload = {"form": form}
        return render(request, "keywordtracking/csv_form.html", payload)
