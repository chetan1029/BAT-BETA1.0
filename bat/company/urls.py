from django.urls import path

from rest_framework_nested import routers

from bat.company.views.setting import AccountSetupViewset

router = routers.DefaultRouter()
router.register('companies', AccountSetupViewset)


app_name = "company"
urlpatterns = router.urls

urlpatterns += [
]
