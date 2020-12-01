from django.contrib import admin

from bat.company.models import (
    Bank,
    Company,
    CompanyPaymentTerms,
    CompanyType,
    HsCode,
    Location,
    Member,
    PackingBox,
    Tax,
    CompanyContract,
    File,
    ComponentMe
)

admin.site.register(Bank)
admin.site.register(Company)
admin.site.register(CompanyPaymentTerms)
admin.site.register(CompanyType)
admin.site.register(Member)
admin.site.register(Location)
admin.site.register(PackingBox)
admin.site.register(HsCode)
admin.site.register(Tax)
admin.site.register(CompanyContract)
admin.site.register(File)
admin.site.register(ComponentMe)
