/** 全局常量与运行时配置。 */

export const SITE_NAME = import.meta.env.VITE_SITE_NAME || '个人工作门户'

/** 后端接口统一前缀（与 server/config/urls.py 的挂载路径保持一致） */
export const API_PREFIX = '/api/core'

/** localStorage 键名 */
export const STORAGE_KEYS = {
  access: 'portal.access',
  refresh: 'portal.refresh',
} as const
