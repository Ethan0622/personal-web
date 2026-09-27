"""门户外壳的序列化器。"""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import AuditLog, ExternalLink, ModulePermission

User = get_user_model()


class ModulePermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModulePermission
        fields = ["id", "code", "name", "module", "order"]


class UserSerializer(serializers.ModelSerializer):
    """用户详情（输出）。

    注意：绝不输出 password；权限以权限码列表形式给出，前端据此渲染菜单。
    """

    role_display = serializers.CharField(source="get_role_display", read_only=True)
    perms = serializers.SerializerMethodField()
    extra_perms = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="code"
    )

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "real_name",
            "email",
            "phone",
            "role",
            "role_display",
            "is_active",
            "date_joined",
            "last_login",
            "perms",
            "extra_perms",
        ]
        read_only_fields = ["id", "date_joined", "last_login", "perms", "extra_perms"]

    def get_perms(self, obj) -> list[str]:
        return sorted(obj.effective_perms)


class UserWriteSerializer(serializers.ModelSerializer):
    """用户创建 / 修改。

    安全要点（针对老系统漏洞）：
    - `role` 只有超级管理员能设置，其他人传了也会被忽略；
    - `is_superuser` / `is_staff` 完全不接受客户端传参；
    - 创建时若未提供密码，则自动生成随机密码并返回，交由管理员转告。
    """

    password = serializers.CharField(
        write_only=True, required=False, allow_blank=True, min_length=8,
        style={"input_type": "password"},
    )
    extra_perms = serializers.SlugRelatedField(
        many=True, required=False, slug_field="code",
        queryset=ModulePermission.objects.all(),
    )

    class Meta:
        model = User
        fields = [
            "id", "username", "password", "real_name", "email",
            "phone", "role", "is_active", "extra_perms",
        ]
        read_only_fields = ["id"]

    def _caller_is_superadmin(self) -> bool:
        request = self.context.get("request")
        return bool(request and request.user.has_perm_code("*"))

    def validate_role(self, value):
        # 非超管提交 role 时直接忽略，保持原值 / 默认值
        if not self._caller_is_superadmin():
            raise serializers.ValidationError("只有超级管理员可以指定角色")
        return value

    def validate_extra_perms(self, value):
        if not self._caller_is_superadmin():
            raise serializers.ValidationError("只有超级管理员可以分配额外权限")
        return value

    def create(self, validated_data):
        extra_perms = validated_data.pop("extra_perms", [])
        password = validated_data.pop("password", "") or None
        user = User.objects.create_user(password=password, **validated_data)
        if extra_perms:
            user.extra_perms.set(extra_perms)
        return user

    def update(self, instance, validated_data):
        extra_perms = validated_data.pop("extra_perms", None)
        password = validated_data.pop("password", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        if password:
            instance.set_password(password)
        instance.save()
        if extra_perms is not None:
            instance.extra_perms.set(extra_perms)
        return instance


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=64)
    password = serializers.CharField(max_length=128, style={"input_type": "password"})


class LoginResponseSerializer(serializers.Serializer):
    """登录响应（用于接口文档展示）。"""

    access = serializers.CharField(help_text="访问令牌")
    refresh = serializers.CharField(help_text="刷新令牌")
    user = UserSerializer()


class MessageSerializer(serializers.Serializer):
    """简单的消息响应。"""

    message = serializers.CharField()


class PortalInfoSerializer(serializers.Serializer):
    site_name = serializers.CharField()
    version = serializers.CharField()


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(max_length=128, style={"input_type": "password"})
    new_password = serializers.CharField(
        max_length=128, min_length=8, style={"input_type": "password"}
    )


class ExternalLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExternalLink
        fields = [
            "id", "title", "url", "icon", "description", "category",
            "order", "is_active", "open_in_new_tab", "required_perm", "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate_url(self, value):
        # 允许 http/https 以及站内相对路径
        if value.startswith(("http://", "https://", "/")):
            return value
        raise serializers.ValidationError("地址需以 http://、https:// 或 / 开头")


class AuditLogSerializer(serializers.ModelSerializer):
    action_display = serializers.CharField(source="get_action_display", read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            "id", "username", "action", "action_display", "method", "path",
            "status_code", "ip", "created_at",
        ]
