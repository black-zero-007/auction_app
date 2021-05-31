# Author:JZW
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response

class MiniLimitOffsetPagination(LimitOffsetPagination):
    default_limit = 10
    max_limit = 50
    limit_query_param = 'limit'
    offset_query_param = 'offset'

    def get_offset(self, request):
        return 0
    def get_paginated_response(self, data):
        return Response(data)