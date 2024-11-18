""""Custom DRF pagination classes"""

from rest_framework.pagination import PageNumberPagination


class FlexiblePagination(PageNumberPagination):
    """Just a custom pagination class"""

    # Page size is 20 by default - can specify this param in GET
    page_size = 20
    page_size_query_param = "page_size"
