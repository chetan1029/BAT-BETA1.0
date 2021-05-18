import csv
from io import StringIO

from django.contrib import admin
from django import forms
from django.urls import path 
from django.utils import timezone
from django.shortcuts import redirect, render


from bat.keywordtracking.models import Keyword, ProductKeyword, ProductKeywordRank, GlobalKeyword
from bat.keywordtracking.import_global_keyword_csv import import_global_keyword_csv, CsvImportForm

admin.site.register(Keyword)
admin.site.register(ProductKeyword)
admin.site.register(ProductKeywordRank)

@admin.register(GlobalKeyword)
class GlobalKeywordAdmin(admin.ModelAdmin):
    change_list_template = "keywordtracking/globalkeywords_changelist.html"

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('import-csv/', self.import_csv),
        ]
        return my_urls + urls

    def import_csv(self, request):
        if request.method == "POST":
            csv_file = request.FILES["csv_file"]
            import_global_keyword_csv(csv_file)
            return redirect("..")
        form = CsvImportForm()
        payload = {"form": form}
        return render(
            request, "keywordtracking/csv_form.html", payload
        )

