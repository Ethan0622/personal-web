/**
 * 统一 HTTP 层。
 *
 * 相比老项目把 axios 包了四遍的写法，这里只用一个实例 + 两个拦截器：
 *   - 请求拦截：自动带上 Bearer token
 *   - 响应拦截：401 自动静默刷新并重放请求；失败统一提示
 */

import axios, { AxiosError, type AxiosInstance, type InternalAxiosRequestConfig } from 'axios'
import { Notify } from 'quasar'

import { API_PREFIX } from '@/shared/config'
import type { ApiErrorBody } from '@/shared/types'

import { clearTokens, getAccessToken, getRefreshToken, setTokens } from './tokens'

/** 会话彻底失效时的回调，由 shell 层注册（跳登录页） */
type UnauthorizedHandler = () => void
let handleUnauthorized: UnauthorizedHandler | null = null

export function setUnauthorizedHandler(handler: UnauthorizedHandler): void {
  handleUnauthorized = handler
}

export const http: AxiosInstance = axios.create({
  baseURL: '/',
  timeout: 20000,
  headers: { 'Content-Type': 'application/json' },
})

http.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

/** 刷新中的 Promise，用于并发请求只刷新一次 */
let refreshing: Promise<string | null> | null = null

async function requestNewAccessToken(): Promise<string | null> {
  const refresh = getRefreshToken()
  if (!refresh) return null
  try {
    // 刻意用裸 axios，不经过本实例的拦截器，避免无限递归
    const { data } = await axios.post<{ access: string; refresh?: string }>(
      `${API_PREFIX}/auth/refresh/`,
      { refresh },
    )
    setTokens(data.access, data.refresh ?? refresh)
    return data.access
  } catch {
    return null
  }
}

function isAuthEndpoint(url: string): boolean {
  return url.includes('/auth/login/') || url.includes('/auth/refresh/')
}

http.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiErrorBody>) => {
    const status = error.response?.status
    const original = error.config as (InternalAxiosRequestConfig & { _retried?: boolean }) | undefined
    const url = original?.url ?? ''

    // ── access token 过期：静默刷新后重放一次 ──
    if (status === 401 && original && !original._retried && !isAuthEndpoint(url)) {
      original._retried = true
      refreshing ??= requestNewAccessToken().finally(() => {
        refreshing = null
      })
      const newToken = await refreshing

      if (newToken) {
        original.headers.Authorization = `Bearer ${newToken}`
        return http.request(original)
      }

      // 刷新也失败 → 会话结束
      clearTokens()
      handleUnauthorized?.()
      return Promise.reject(error)
    }

    // ── 其他错误：统一提示（登录接口交给页面自行展示，避免重复弹窗）──
    if (!isAuthEndpoint(url)) {
      const message =
        error.response?.data?.message ||
        (status === 403 ? '你没有执行该操作的权限' : '') ||
        (error.code === 'ECONNABORTED' ? '请求超时，请检查网络' : '') ||
        '请求失败，请稍后重试'
      Notify.create({ type: 'negative', message, position: 'top', timeout: 3000 })
    }

    return Promise.reject(error)
  },
)

/** 便捷方法：直接拿到 data */
export const api = {
  get: <T>(url: string, params?: Record<string, unknown>) =>
    http.get<T>(url, { params }).then((r) => r.data),
  post: <T>(url: string, data?: unknown) => http.post<T>(url, data).then((r) => r.data),
  patch: <T>(url: string, data?: unknown) => http.patch<T>(url, data).then((r) => r.data),
  put: <T>(url: string, data?: unknown) => http.put<T>(url, data).then((r) => r.data),
  delete: <T>(url: string) => http.delete<T>(url).then((r) => r.data),
}
