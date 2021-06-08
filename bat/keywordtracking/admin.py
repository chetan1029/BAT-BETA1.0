import csv
from io import StringIO
from django import forms

from django import forms
from django.contrib import admin
from django.shortcuts import redirect, render
from django.urls import path

from bat.keywordtracking.models import (
    GlobalKeyword,
    Keyword,
    ProductKeyword,
    ProductKeywordRank,
)

# from bat.keywordtracking.utils import clean_global_keyword

from bat.keywordtracking.import_global_keyword_csv import (
    CsvImportForm,
    import_global_keyword_csv,
)

admin.site.register(Keyword)
admin.site.register(ProductKeyword)
admin.site.register(ProductKeywordRank)


# class CsvImportForm(forms.Form):
#     csv_file = forms.FileField()


# @admin.register(GlobalKeyword)
# class GlobalKeywordAdmin(admin.ModelAdmin):
#     change_list_template = "keywordtracking/globalkeywords_changelist.html"

#     def get_urls(self):
#         urls = super().get_urls()
#         my_urls = [path("import-csv/", self.import_csv)]
#         return my_urls + urls

#     def import_csv(self, request):
#         if request.method == "POST":
#             csv_file = request.FILES["csv_file"]
#             clean_csv_file, department = clean_global_keyword(csv_file)
#             GlobalKeyword.objects.filter(department=department).delete()
#             GlobalKeyword.objects.bulk_copy(clean_csv_file)
#             return redirect("..")
#         form = CsvImportForm()
#         payload = {"form": form}
#         return render(request, "keywordtracking/csv_form.html", payload)



@admin.register(GlobalKeyword)
class GlobalKeywordAdmin(admin.ModelAdmin):
    change_list_template = "keywordtracking/globalkeywords_changelist.html"

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [path("import-csv/", self.import_csv)]
        return my_urls + urls

    def import_csv(self, request):
        if request.method == "POST":
            csv_file = request.FILES["csv_file"]
            import_global_keyword_csv(csv_file)
            return redirect("..")
        form = CsvImportForm()
        payload = {"form": form}
        return render(request, "keywordtracking/csv_form.html", payload)