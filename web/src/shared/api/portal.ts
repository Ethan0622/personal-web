/**
 * 门户级（外壳）接口客户端。
 *
 * 放在 shared 层是因为"外链入口"属于门户外壳能力，
 * 会被多个模块（工作台、外链入口页）复用 —— 各模块禁止互相 import。
 */

import { api } from './http'

import type { ExternalLink, Paginated, PortalInfo } from '@/shared/types'

/** 门户公开信息（无需登录） */
export function fetchPortalInfo() {
  return api.get<PortalInfo>('/api/core/portal/')
}

/** 取回当前用户有权访问的外链入口 */
export function fetchExternalLinks() {
  return api.get<Paginated<ExternalLink>>('/api/core/links/', { page_size: 200 })
}

export function createExternalLink(payload: Partial<ExternalLink>) {
  return api.post<ExternalLink>('/api/core/links/', payload)
}

export function updateExternalLink(id: number, payload: Partial<ExternalLink>) {
  return api.patch<ExternalLink>(`/api/core/links/${id}/`, payload)
}

export function removeExternalLink(id: number) {
  return api.delete<void>(`/api/core/links/${id}/`)
}
