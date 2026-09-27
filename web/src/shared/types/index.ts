/** 通用类型定义。 */

/** 后端统一错误响应体（见 server/apps/core/exceptions.py） */
export interface ApiErrorBody {
  code: string
  message: string
  errors?: unknown
}

/** DRF 分页响应 */
export interface Paginated<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

/** 角色 */
export type PortalRole = 'superadmin' | 'admin' | 'staff' | 'guest'

/** 当前用户 */
export interface PortalUser {
  id: number
  username: string
  real_name: string
  email: string
  phone: string
  role: PortalRole
  role_display: string
  is_active: boolean
  date_joined: string
  last_login: string | null
  /** 生效的权限码，超管会包含通配符 "*" */
  perms: string[]
  extra_perms: string[]
}

/** 外链入口 */
export interface ExternalLink {
  id: number
  title: string
  url: string
  icon: string
  description: string
  category: string
  order: number
  is_active: boolean
  open_in_new_tab: boolean
  required_perm: string
  created_at?: string
}

/** 登录响应 */
export interface LoginResult {
  access: string
  refresh: string
  user: PortalUser
}

/** 门户公开信息 */
export interface PortalInfo {
  site_name: string
  version: string
}
