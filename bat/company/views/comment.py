from django.contrib.contenttypes.models import ContentType
from bat.comments.views import BaseCommentViewSet


class CompanyContractCommentsViewSet(BaseCommentViewSet):
    """
    View set to save comments of CompanyContract
    """
    allow_create_permission_list = ["comment_company_contract"]
    allow_list_permission_list = ["view_company_contract"]

    def get_content_type(self):
        return ContentType.objects.get(
            app_label='company', model='companycontract')
