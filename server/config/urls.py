"""URL 总入口 —— 新增业务模块时在这里追加一行 include 即可。"""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    # ── 门户外壳 ────────────────────────────────────────────────
    path("api/core/", include("apps.core.urls")),
    # ── 业务模块（按需追加）─────────────────────────────────────
    # path("api/exam/", include("apps.exam.urls")),      # 考试模块
    # path("api/canteen/", include("apps.canteen.urls")),# 食堂管理模块
    # ── 接口文档 ────────────────────────────────────────────────
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]
