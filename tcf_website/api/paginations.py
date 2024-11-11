""""Custom DRF pagination classes"""

import warnings

from rest_framework.pagination import PageNumberPagination


class FlexiblePagination(PageNumberPagination):
    """Just a custom pagination class"""

    # Page size is 20 by default - can specify this param in GET
    page_size = 20
    page_size_query_param = "page_size"

    def __init__(self, *args, **kwargs):
        warnings.warn(
            "The FlexiblePagination class is deprecated."
            + "Please use Paginator from django.core.paginator instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)
