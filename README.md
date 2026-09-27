# 个人工作门户

一个**模块化单体**（Modular Monolith）的个人工作台：一个统一入口、一次登录，
通过不同路由通往各个业务模块与外部平台。

前身是本科毕业设计《现代教育技术自适应测试系统》，现在把它从"单科考试平台"
升级为承载日常工作场景的门户 —— 考试系统将成为其中第一个业务模块。

---

## 目录结构

```
work-portal/
├── server/                      # 后端：Django 5.2 LTS 模块化单体
│   ├── config/                  # 工程配置
│   │   ├── settings/            # base / dev / prod 三层配置（密钥全部走环境变量）
│   │   ├── urls.py              # ★ 新增模块在此 include 一行
│   │   ├── wsgi.py / asgi.py
│   ├── apps/
│   │   ├── core/                # ★ 门户外壳：统一用户、权限、审计、外链入口
│   │   │   ├── perms.py         # 权限码目录（新增模块权限在此登记）
│   │   │   ├── models.py        # User / ModulePermission / ExternalLink / AuditLog
│   │   │   ├── permissions.py   # 权限类 + 归属校验基类
│   │   │   ├── authentication.py
│   │   │   ├── middleware.py    # 审计日志
│   │   │   ├── checks.py        # ★ 未声明权限的接口会在启动时报警
│   │   │   ├── views.py / urls.py / serializers.py / admin.py
│   │   │   └── tests/           # 权限回归测试（29 个用例）
│   │   └── ...                  # 后续业务模块（exam / canteen / assets ...）
│   ├── pyproject.toml
│   ├── .env.example             # 复制为 .env 后填写
│   └── manage.py
│
├── web/                         # 前端：Vite + Vue 3.5 + Quasar
│   ├── src/
│   │   ├── shell/               # ★ 门户外壳
│   │   │   ├── registry.ts      # ★ 模块注册中心：新增平台在这里加一行
│   │   │   ├── types.ts         # ModuleDescriptor 定义
│   │   │   ├── useModules.ts    # 模块可见性计算
│   │   │   ├── router.ts        # 路由汇总 + 登录/权限守卫
│   │   │   ├── auth.ts          # 认证状态
│   │   │   ├── layouts/         # 主布局（顶栏 + 侧栏 + 内容区）
│   │   │   └── views/           # 登录页 / 个人设置 / 403 / 404
│   │   ├── modules/             # ★ 业务模块（每个自包含）
│   │   │   ├── dashboard/       # 工作台
│   │   │   └── links/           # 外链入口
│   │   └── shared/              # 共享层
│   │       ├── api/             # http 实例、token、门户级接口
│   │       ├── types/           # 公共类型
│   │       └── components/      # 公共组件
│   ├── vite.config.ts
│   └── package.json
│
└── deploy/                      # 部署
    ├── nginx/portal.conf        # Nginx 配置（含备案后启用 HTTPS 的段落）
    ├── systemd/work-portal.service
    ├── mysql/tuning.cnf         # 2G 内存的 MySQL 调优
    ├── backup.sh                # 每日备份（可上传 OSS）
    └── README.md                # ★ 部署步骤

另外两个目录：

- `reference/` —— 老毕设的两个仓库（`test_system` 后端、`test_system_ui` 前端），
  迁移考试模块时作为源码参考，不参与构建，可以随时删掉
- `docs/reports/` —— 前期分析报告（项目评估、安全审计、目标架构蓝图）
```

---

## 技术栈

| 层 | 选型 | 说明 |
|---|---|---|
| 前端构建 | Vite 8 | 替代老项目的 Vue CLI 4.5（webpack 4 在 Node 22 上无法构建） |
| 前端框架 | Vue 3.5 + TypeScript 5 | 沿用，仅升级 |
| UI 组件库 | Quasar 2.33 | 沿用（26 个页面的写法都用得上） |
| 状态管理 | Pinia 4 | 替代老项目的 Pinia 2 |
| HTTP | Axios 1.20 | 替换有 SSRF 漏洞的 0.21.4 |
| 后端框架 | Django 5.2 LTS | 支持到 2028-04；替代已 EOL 的 3.2 |
| API | Django REST Framework 3.18 | |
| 认证 | simplejwt 5.5 | 替代停更 9 年的 djangorestframework-jwt |
| API 文档 | drf-spectacular | 替代已弃用的 drf-yasg |
| 依赖管理 | uv（推荐） | 替代裸 pip；老项目连 requirements.txt 都没有 |
| 代码规范 | ruff | 替代 flake8 + isort + black |

---

## 本地运行（Windows）

> 项目位置：`D:\career\personal-web`

### 一键启动

双击项目根目录的 **`dev.bat`**，它会打开两个命令行窗口：

- `Work Portal [Backend :8000]` — Django 后端
- `Work Portal [Frontend :5173]` — Vite 前端

等几秒后浏览器访问 **http://127.0.0.1:5173**

默认账号：**`admin` / `Portal@2026`** ← **登录后请立即修改密码**

### 前提条件

| 需要 | 当前状态 | 说明 |
|---|---|---|
| Python 3.12 | ✅ 已就绪 | 已在 `server\.venv` 建好虚拟环境并装好全部依赖 |
| Node.js 22 LTS | ⚠️ **尚未安装** | `dev-frontend.bat` 会自动回退使用 WorkBuddy 内置的 Node；若要独立运行前端，请到 https://nodejs.org/ 下载 **LTS** 版安装 |

### 手动启动（等价于脚本）

**窗口 1 · 后端**

```bat
cd /d D:\career\personal-web\server
.venv\Scripts\python.exe manage.py migrate
.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

**窗口 2 · 前端**

```bat
cd /d D:\career\personal-web\web
npm install
npm run dev
```

前端开发服务器会把 `/api` 请求**代理**到 `http://127.0.0.1:8000`，
所以本地开发**完全不需要配置跨域**。

### 常用地址

| 用途 | 地址 |
|---|---|
| 门户首页 | http://127.0.0.1:5173 |
| Django 后台 | http://127.0.0.1:8000/admin/ |
| 接口文档（Swagger） | http://127.0.0.1:8000/api/docs/ |

### 其他常用命令

```bat
cd /d D:\career\personal-web\server

.venv\Scripts\python.exe manage.py check            :: 系统检查（含"未声明权限"检查）
.venv\Scripts\python.exe manage.py test apps.core   :: 权限回归测试（29 个用例）
.venv\Scripts\python.exe manage.py createsuperuser  :: 新建管理员账号
.venv\Scripts\python.exe manage.py makemigrations   :: 新增模型后生成迁移
```

改密码也可以走界面：右上角头像 → 个人设置 → 修改密码。

### 首次安装依赖（仅在新机器上需要）

```bat
:: 后端
cd /d D:\career\personal-web\server
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -e ".[dev]"

:: 前端
cd /d D:\career\personal-web\web
npm install --registry=https://registry.npmmirror.com
```

> 国内用镜像源会快很多。注意：npm 官方源与国内镜像的同步有延迟，
> 镜像上可能缺少最新补丁版（例如 quasar 镜像停在 2.33.1，官方已是 2.33.2），
> 所以依赖版本写的是 `^2.33.0` 而不是钉死最新版。

---

## 如何新增一个模块

这是本项目的核心设计。假设要新增「食堂管理」模块：

### 1. 后端（约 5 分钟）

```bash
cd server/apps
mkdir -p canteen/migrations
touch canteen/__init__.py canteen/migrations/__init__.py
```

新建 `apps/canteen/models.py`、`views.py`、`urls.py`、`serializers.py`、`apps.py`，然后：

```python
# 1) config/settings/base.py
LOCAL_APPS = [
    "apps.core",
    "apps.canteen",        # ← 加这一行
]

# 2) config/urls.py
path("api/canteen/", include("apps.canteen.urls")),   # ← 加这一行

# 3) apps/core/perms.py —— 登记该模块的权限码
class PermCode:
    ...
    CANTEEN_VIEW = "canteen.view"
    CANTEEN_MANAGE = "canteen.manage"

PERMISSION_CATALOG = [
    ...
    (PermCode.CANTEEN_VIEW, "食堂：查看", "食堂模块", 210),
    (PermCode.CANTEEN_MANAGE, "食堂：管理", "食堂模块", 220),
]
```

```python
# 4) 视图里声明权限（不写会在启动时收到 core.W001 警告）
class MenuItemViewSet(ActionPermsMixin, viewsets.ModelViewSet):
    PERMS_BY_ACTION = {
        "list": [PermCode.CANTEEN_VIEW],
        "create": [PermCode.CANTEEN_MANAGE],
        ...
    }
```

```bash
python manage.py makemigrations canteen
python manage.py migrate        # 顺带把新权限码写入数据库
```

### 2. 前端（约 3 分钟）

```bash
mkdir -p web/src/modules/canteen/views
```

```typescript
// web/src/modules/canteen/index.ts
import type { ModuleDescriptor } from '@/shell/types'

export default {
  key: 'canteen',
  title: '食堂管理',
  icon: 'restaurant',
  kind: 'internal',
  path: '/canteen',
  permission: 'canteen.view',
  order: 30,
  description: '留样台账、食谱、员工管理',
  routes: [
    {
      path: '/canteen',
      name: 'canteen',
      component: () => import('./views/CanteenView.vue'),
      meta: { title: '食堂管理', permissions: ['canteen.view'] },
    },
  ],
} satisfies ModuleDescriptor
```

```typescript
// web/src/shell/registry.ts —— 加一行 import + 加一行数组元素
import canteenModule from '@/modules/canteen'

export const modules: ModuleDescriptor[] = [
  dashboardModule,
  linksModule,
  canteenModule,          // ← 加这一行
]
```

**完成。** 侧栏菜单、路由、权限过滤、工作台卡片全部自动生效，
老模块的代码一行都不用改。

### 3. 只想加一个外部平台入口？

不需要写任何代码，两种方式任选：

- 登录门户 → 「外链入口」页 → 右上角「添加入口」
- Django 后台 → 外链入口 → 新增

---

## 权限体系

### 设计原则：默认拒绝

每个接口必须**显式声明**所需权限，否则只能拿到"仅登录"的最低门槛，
并且启动时的系统检查会给出 `core.W001` 警告：

```
python manage.py check

WARNINGS:
<class 'apps.xxx.views.SomeView'>: (core.W001) apps.xxx.views.SomeView 未声明权限。
    HINT: 请设置 required_perms = ['模块.资源.动作']（需特定权限），
          或设置 allow_any = True（公开接口）。默认拒绝是本项目的安全基线。
```

这条机制是专门为防止重演老系统的问题而设计的 ——
老系统有 7 个高危漏洞，根因都是"忘了给教师专属接口加权限类"。

### 角色与权限码

| 角色 | 默认权限 |
|---|---|
| `superadmin` 超级管理员 | 通配符 `*`，拥有一切权限 |
| `admin` 管理员 | 门户内的大部分管理权限 |
| `staff` 普通成员 | 查看门户与外链入口 |
| `guest` 访客 | 仅访问门户 |

权限码格式为 `模块.资源.动作`，例如
`portal.user.manage`、`exam.itembank.manage`、`canteen.manage`。
角色的默认权限定义在 `apps/core/perms.py` 的 `ROLE_DEFAULT_PERMS`，
超出角色默认范围的授权通过后台为用户单独分配「额外权限」。

### 归属校验

业务模块涉及"只能看/改自己的数据"时，直接复用现成的权限类：

```python
from apps.core.permissions import IsObjectOwner

class MyTestViewSet(viewsets.ModelViewSet):
    owner_field = 'user'          # 支持点号路径，如 'test.user'
    permission_classes = [IsAuthenticated, IsObjectOwner]
```

---

## 迁移映射（老项目 → 新项目）

| 老项目 | 新项目 | 处理方式 |
|---|---|---|
| `test_system_ui/src/views/*.vue` | `web/src/modules/exam/views/` | 搬运 + 适配为模块页面 |
| `test_system_ui/src/store/*.ts` | `web/src/modules/exam/stores/` | 搬运 + 改用 Pinia 4 |
| `test_system_ui/src/api/index.ts` | `web/src/shared/api/http.ts` | **重构**：统一 axios 实例 + 拦截器 |
| `test_system_ui/src/api/baseUrl.ts` | `web/src/shared/config.ts` | **删除硬编码 IP**，改用环境变量 + 代理 |
| `test_system_ui/src/router/index.ts` | `modules/exam/routes.ts` + `shell/registry.ts` | 拆分 |
| `test_system_ui/docs/` | `docs/` | VuePress 2 beta → VitePress |
| `test_system/users/` | `apps/core/` + `apps/exam/` | 用户上提到 core，考试相关用 profile 扩展 |
| `test_system/itembank/` | `apps/exam/itembank/` | 搬运 + xlrd → openpyxl |
| `test_system/classes/` | `apps/exam/classes/` | 搬运 + 移除硬编码默认密码 |
| `test_system/testing/` | `apps/exam/testing/` | 搬运 + **补归属校验 + 修算法缺陷** |
| `test_system/test_system/settings.py` | `server/config/settings/*` | 拆分，密钥外置 |
| `test_system/uwsgi.ini` | `deploy/systemd/` + Gunicorn | 替换 |
| `test_system/static/`（8.3MB） | — | 删除并入 `.gitignore` |

---

## 安全说明（与老项目的关键差异）

老系统公开仓库时暴露了以下问题，本项目逐条做了防护：

| 老项目问题 | 本项目对策 |
|---|---|
| SECRET_KEY 硬编码且为默认值 | 从环境变量读取，缺失直接启动失败 |
| 数据库密码、服务器密码明文入库 | 全部走 `.env`，`.env` 已在 `.gitignore` |
| 注册接口可传 `type=1` 注册成管理员 | 无公开注册接口；`role` 仅超管可设；`is_superuser` 不接受客户端传参 |
| `user_detail/<id>/` 可改任意用户密码 | 用户管理需 `portal.user.manage`；且不能删除自己 |
| `user_list/` 无需认证泄露全量用户 | 用户列表需 `portal.user.view` |
| 教师专属接口只有 `IsAuthenticated` | `ActionPermsMixin` 按动作声明权限 + 启动检查报警 |
| 考试接口无归属校验 | 提供 `IsObjectOwner` 基类，业务模块直接复用 |
| 明文 HTTP、硬编码 IP | 用 IP 访问时也不暴露敏感信息；配置全部外置，换机器不改代码 |
| 无审计日志 | `AuditLogMiddleware` 记录全部写操作（含操作人、IP、路径、状态码） |
| 零测试 | 29 个权限回归测试锁住上述每一条 |

---

## 部署

见 [`deploy/README.md`](deploy/README.md)。

---

## 当前进度

- [x] 阶段Ⅰ-1 后端骨架（Django 5.2 + core 模块 + 29 个测试全部通过）
- [x] 阶段Ⅰ-2 前端骨架（Vite 8 + Vue 3.5 + Quasar 2.33 + 模块注册机制）
- [x] 阶段Ⅰ-3 工作台模块 + 外链入口模块
- [x] 阶段Ⅰ-4 部署文件与文档
- [x] 阶段Ⅰ-5 本地环境跑通（后端 + 前端 + 代理链路实测通过）
- [ ] 阶段Ⅱ　迁移考试模块（`apps/exam` + `modules/exam`）
- [ ] 阶段Ⅲ　部署到阿里云轻量服务器
- [ ] 阶段Ⅳ　按需增加工作模块

### 验证记录（2026-09-26）

| 项目 | 结果 |
|---|---|
| 后端系统检查 | `manage.py check` 无告警 |
| 权限回归测试 | 29 个用例全部通过 |
| 接口文档生成 | drf-spectacular 零告警，13 条路径 + JWT 认证方案 |
| 前端类型检查 | `vue-tsc --noEmit` 通过 |
| 前端生产构建 | 234 个模块，约 3 秒，分包正常 |
| 端到端链路 | 经 Vite 代理登录 → 取当前用户 → 取外链入口，全部成功 |
| 安全行为实测 | 未登录访问受保护接口返回 401；密码错误返回统一提示 |

