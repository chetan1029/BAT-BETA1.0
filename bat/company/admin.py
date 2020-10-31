from django.contrib import admin


from bat.company.models import (Bank, Category, Company, CompanyPaymentTerms,
                                CompanyType, Member, Location, PackingBox, HsCode, Tax)

admin.site.register(Bank)
admin.site.register(Category)
admin.site.register(Company)
admin.site.register(CompanyPaymentTerms)
admin.site.register(CompanyType)
admin.site.register(Member)
admin.site.register(Location)
admin.site.register(PackingBox)
admin.site.register(HsCode)
admin.site.register(Tax)
