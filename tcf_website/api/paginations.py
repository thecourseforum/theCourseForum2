""""Custom DRF pagination classes"""
from rest_framework.pagination import PageNumberPagination


class MyPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
