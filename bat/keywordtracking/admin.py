from django.contrib import admin

from bat.keywordtracking.models import Keyword, ProductKeyword, ProductKeywordRank, GlobalKeyword

admin.site.register(Keyword)
admin.site.register(ProductKeyword)
admin.site.register(ProductKeywordRank)
admin.site.register(GlobalKeyword)
