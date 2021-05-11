from django.contrib import admin

from bat.keywordtracking.models import Keyword, ProductKeyword, ProductKeywordRank

admin.site.register(Keyword)
admin.site.register(ProductKeyword)
admin.site.register(ProductKeywordRank)
