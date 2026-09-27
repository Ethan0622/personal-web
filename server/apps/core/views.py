"""门户外壳接口：认证、当前用户、权限目录、外链入口、用户与审计日志管理。"""

from django.contrib.auth import authenticate, get_user_model
from django.db.models import Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from .authentication import set_audit_user
from .middleware import get_client_ip
from .models import AuditLog, ExternalLink, ModulePermission
from .perms import PermCode
from .permissions import ActionPermsMixin
from .serializers import (
    AuditLogSerializer,
    ChangePasswordSerializer,
    ExternalLinkSerializer,
    LoginResponseSerializer,
    LoginSerializer,
    MessageSerializer,
    ModulePermissionSerializer,
    PortalInfoSerializer,
    UserSerializer,
    UserWriteSerializer,
)

User = get_user_model()


class InvalidCredentials(APIException):
    """登录凭证错误。

    刻意不使用 DRF 的 AuthenticationFailed：DRF 在视图未配置认证类时
    会把 AuthenticationFailed 的状态码改写成 403，而登录失败语义上应为 401。
    """

    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = "账号或密码错误"
    default_code = "invalid_credentials"


def _issue_tokens(user) -> dict:
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


# ════════════════════════════════════════════════════════ 认证


class PortalInfoView(APIView):
    """门户公开信息，供登录页展示（无需登录）。"""

    allow_any = True
    authentication_classes = []
    permission_classes = []

    @extend_schema(responses={200: PortalInfoSerializer}, summary="门户信息（公开）")
    def get(self, request):
        from django.conf import settings

        return Response(
            {
                "site_name": getattr(settings, "SITE_NAME", "个人工作门户"),
                "version": "1.0.0",
            }
        )


class LoginView(APIView):
    """账号密码登录。"""

    allow_any = True
    authentication_classes = []
    permission_classes = []

    @extend_schema(
        request=LoginSerializer,
        responses={200: LoginResponseSerializer, 401: MessageSerializer},
        summary="登录",
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]

        user = authenticate(request, username=username, password=password)
        if user is None:
            # 统一提示，不区分"账号不存在"和"密码错误"，避免账号枚举
            raise InvalidCredentials()
        if not user.is_active:
            raise InvalidCredentials("该账号已被停用")

        user.last_login = timezone.now()
        user.last_login_ip = get_client_ip(request)
        user.save(update_fields=["last_login", "last_login_ip"])

        # 登录接口没有认证类，需手动登记操作人，审计日志才记得到
        set_audit_user(request, user)

        tokens = _issue_tokens(user)
        return Response(
            {
                "access": tokens["access"],
                "refresh": tokens["refresh"],
                "user": UserSerializer(user, context={"request": request}).data,
            },
            status=status.HTTP_200_OK,
        )


class RefreshView(TokenRefreshView):
    """刷新 access token。"""

    allow_any = True
    authentication_classes = []
    permission_classes = []


class LogoutView(APIView):
    """登出：把 refresh token 加入黑名单。"""

    required_perms = [PermCode.PORTAL_VIEW]

    @extend_schema(request=None, responses={200: MessageSerializer}, summary="登出")
    def post(self, request):
        raw = request.data.get("refresh")
        if raw:
            try:
                RefreshToken(raw).blacklist()
            except Exception:
                # token 已失效或格式不对，对登出而言不算错误
                pass
        return Response({"message": "已登出"}, status=status.HTTP_200_OK)


class MeView(APIView):
    """当前登录用户信息（含权限码列表，前端据此过滤模块）。"""

    required_perms = [PermCode.PORTAL_VIEW]

    @extend_schema(responses={200: UserSerializer}, summary="获取当前用户")
    def get(self, request):
        return Response(UserSerializer(request.user, context={"request": request}).data)

    @extend_schema(
        request=UserWriteSerializer,
        responses={200: UserSerializer},
        summary="修改自己的资料",
    )
    def patch(self, request):
        # 只允许改自己的基础资料，且不接受 role / is_active / password 走这里
        allowed = {"real_name", "email", "phone"}
        payload = {k: v for k, v in request.data.items() if k in allowed}
        if not payload:
            raise ValidationError("没有可修改的字段")
        for field, value in payload.items():
            setattr(request.user, field, value)
        request.user.save(update_fields=list(payload.keys()))
        return Response(UserSerializer(request.user, context={"request": request}).data)


class ChangePasswordView(APIView):
    """修改自己的密码。"""

    required_perms = [PermCode.PORTAL_VIEW]

    @extend_schema(
        request=ChangePasswordSerializer,
        responses={200: MessageSerializer},
        summary="修改密码",
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(serializer.validated_data["old_password"]):
            raise ValidationError({"old_password": "原密码不正确"})
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])
        return Response({"message": "密码已更新，请重新登录"}, status=status.HTTP_200_OK)


class PermissionCatalogView(APIView):
    """权限目录，供后台分配权限时使用。"""

    required_perms = [PermCode.PORTAL_USER_VIEW]

    @extend_schema(responses={200: ModulePermissionSerializer(many=True)}, summary="权限目录")
    def get(self, request):
        qs = ModulePermission.objects.all()
        return Response(ModulePermissionSerializer(qs, many=True).data)


# ════════════════════════════════════════════════════════ 外链入口


class ExternalLinkViewSet(ActionPermsMixin, viewsets.ModelViewSet):
    """外链入口。

    这就是用来"留口子"的地方：以后要加学校 OA、企业微信、云盘等入口，
    直接在后台新增记录即可，前端不需要改代码。
    """

    queryset = ExternalLink.objects.all()
    serializer_class = ExternalLinkSerializer
    default_perms = [PermCode.PORTAL_LINKS_VIEW]
    PERMS_BY_ACTION = {
        "list": [PermCode.PORTAL_LINKS_VIEW],
        "retrieve": [PermCode.PORTAL_LINKS_VIEW],
        "create": [PermCode.PORTAL_LINKS_MANAGE],
        "update": [PermCode.PORTAL_LINKS_MANAGE],
        "partial_update": [PermCode.PORTAL_LINKS_MANAGE],
        "destroy": [PermCode.PORTAL_LINKS_MANAGE],
    }

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        # 管理者可见全部（含停用项），普通用户只见自己有权访问的启用项
        if user.has_perm_code(PermCode.PORTAL_LINKS_MANAGE):
            return qs
        held = user.effective_perms
        qs = qs.filter(is_active=True)
        if "*" in held:
            return qs
        return qs.filter(Q(required_perm__in=held) | Q(required_perm=""))


# ════════════════════════════════════════════════════════ 用户管理


class UserViewSet(ActionPermsMixin, viewsets.ModelViewSet):
    """用户管理（后台）。创建用户时角色只有超管能指定。"""

    queryset = User.objects.all().prefetch_related("extra_perms")
    default_perms = [PermCode.PORTAL_USER_VIEW]
    PERMS_BY_ACTION = {
        "list": [PermCode.PORTAL_USER_VIEW],
        "retrieve": [PermCode.PORTAL_USER_VIEW],
        "create": [PermCode.PORTAL_USER_MANAGE],
        "update": [PermCode.PORTAL_USER_MANAGE],
        "partial_update": [PermCode.PORTAL_USER_MANAGE],
        "destroy": [PermCode.PORTAL_USER_MANAGE],
    }
    search_fields = ["username", "real_name", "email", "phone"]
    filterset_fields = ["role", "is_active"]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return UserWriteSerializer
        return UserSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(
                Q(username__icontains=search)
                | Q(real_name__icontains=search)
                | Q(email__icontains=search)
            )
        return qs

    def perform_destroy(self, instance):
        # 不允许删除自己，避免把唯一的超管锁在门外
        if instance == self.request.user:
            raise ValidationError("不能删除当前登录的账号")
        instance.delete()


# ════════════════════════════════════════════════════════ 审计日志


class AuditLogViewSet(ActionPermsMixin, viewsets.ReadOnlyModelViewSet):
    """审计日志（只读）。"""

    queryset = AuditLog.objects.select_related("user").all()
    serializer_class = AuditLogSerializer
    default_perms = [PermCode.PORTAL_AUDIT_VIEW]
    PERMS_BY_ACTION = {
        "list": [PermCode.PORTAL_AUDIT_VIEW],
        "retrieve": [PermCode.PORTAL_AUDIT_VIEW],
    }

    def get_queryset(self):
        qs = super().get_queryset()
        action = self.request.query_params.get("action")
        if action:
            qs = qs.filter(action=action)
        username = self.request.query_params.get("username")
        if username:
            qs = qs.filter(username__icontains=username)
        return qs
