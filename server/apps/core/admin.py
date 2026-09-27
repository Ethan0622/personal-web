"""后台管理。用于初始化数据与日常维护（外链入口就是在这里加的）。"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import AuditLog, ExternalLink, ModulePermission, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ["-date_joined"]
    list_display = ["username", "real_name", "role", "is_active", "is_staff", "date_joined"]
    list_filter = ["role", "is_active", "is_staff"]
    search_fields = ["username", "real_name", "email", "phone"]
    filter_horizontal = ["extra_perms"]
    readonly_fields = ["last_login", "date_joined", "last_login_ip"]

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("个人信息", {"fields": ("real_name", "email", "phone")}),
        (
            "权限",
            {
                "fields": ("role", "extra_perms", "is_active", "is_staff", "is_superuser"),
                "description": "角色决定默认权限，额外授权用于精细放权。超级管理员拥有全部权限。",
            },
        ),
        ("记录", {"fields": ("last_login", "last_login_ip", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "real_name", "role", "password1", "password2"),
            },
        ),
    )


@admin.register(ModulePermission)
class ModulePermissionAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "module", "order"]
    list_filter = ["module"]
    search_fields = ["code", "name"]
    ordering = ["order"]

    def has_add_permission(self, request):
        # 权限项由代码目录中的 PERMISSION_CATALOG 统一维护，不允许手工添加
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ExternalLink)
class ExternalLinkAdmin(admin.ModelAdmin):
    list_display = ["title", "category", "url", "order", "is_active", "required_perm"]
    list_filter = ["category", "is_active"]
    search_fields = ["title", "url", "description"]
    ordering = ["category", "order"]
    list_editable = ["order", "is_active"]
    fieldsets = (
        (None, {"fields": ("title", "url", "icon", "description")}),
        ("显示", {"fields": ("category", "order", "is_active", "open_in_new_tab")}),
        ("权限", {"fields": ("required_perm",)}),
    )


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["created_at", "username", "action", "method", "path", "status_code", "ip"]
    list_filter = ["action", "method"]
    search_fields = ["username", "path", "ip"]
    date_hierarchy = "created_at"
    ordering = ["-created_at"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        # 允许清理历史日志
        return True
