"""分页。

支持 ?page_size= 参数，便于前端一次取回全部（如外链入口、权限目录这类小数据集）。
"""

from rest_framework.pagination import PageNumberPagination


class PortalPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 200
