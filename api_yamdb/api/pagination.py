from rest_framework.pagination import PageNumberPagination

from api_yamdb.settings import PAGINATOR_PAGE_ITEMS_COUNT


class ReviewCommentPagination(PageNumberPagination):
    page_size = PAGINATOR_PAGE_ITEMS_COUNT
