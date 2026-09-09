from rest_framework.pagination import LimitOffsetPagination


class BoundedLimitOffsetPagination(LimitOffsetPagination):
    max_limit = 100
