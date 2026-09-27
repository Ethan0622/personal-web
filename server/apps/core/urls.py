from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AuditLogViewSet,
    ChangePasswordView,
    ExternalLinkViewSet,
    LoginView,
    LogoutView,
    MeView,
    PermissionCatalogView,
    PortalInfoView,
    RefreshView,
    UserViewSet,
)

router = DefaultRouter()
router.register("links", ExternalLinkViewSet, basename="external-link")
router.register("users", UserViewSet, basename="user")
router.register("audit-logs", AuditLogViewSet, basename="audit-log")

urlpatterns = [
    # 公开
    path("portal/", PortalInfoView.as_view(), name="portal-info"),
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/refresh/", RefreshView.as_view(), name="auth-refresh"),
    # 需登录
    path("auth/logout/", LogoutView.as_view(), name="auth-logout"),
    path("auth/me/", MeView.as_view(), name="auth-me"),
    path("auth/change-password/", ChangePasswordView.as_view(), name="auth-change-password"),
    path("auth/permissions/", PermissionCatalogView.as_view(), name="auth-permissions"),
    # 资源
    path("", include(router.urls)),
]
