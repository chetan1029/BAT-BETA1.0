from django.contrib import admin
from django import forms
from django.urls import path 
from django.utils import timezone
from django.shortcuts import redirect, render


from bat.keywordtracking.models import Keyword, ProductKeyword, ProductKeywordRank, GlobalKeyword

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
        my_urls = [
            path('import-csv/', self.import_csv),
        ]
        return my_urls + urls

    def import_csv(self, request):
        if request.method == "POST":
            csv_file = request.FILES["csv_file"]
            GlobalKeyword.objects.from_csv(
            csv_file,
            mapping=dict(department='Department',
                        name='Search Term',
                        frequency="Search Frequency Rank",
                        asin_1="#1 Clicked ASIN",
                        asin_2="#2 Clicked ASIN",
                        asin_3="#3 Clicked ASIN"),
            static_mapping={"create_date": timezone.now().isoformat()},
            drop_indexes=False,
            drop_constraints=False
            )
            return redirect("..")
        form = CsvImportForm()
        payload = {"form": form}
        return render(
            request, "keywordtracking/csv_form.html", payload
        )

