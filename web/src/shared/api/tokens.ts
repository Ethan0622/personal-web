/**
 * Token 存储。
 *
 * 单独成模块是为了打破循环依赖：http 拦截器需要读写 token，
 * 而 auth store 又需要 http —— 两者都只依赖这里，就不会互相引用。
 */

import { STORAGE_KEYS } from '@/shared/config'

export function getAccessToken(): string {
  return localStorage.getItem(STORAGE_KEYS.access) ?? ''
}

export function getRefreshToken(): string {
  return localStorage.getItem(STORAGE_KEYS.refresh) ?? ''
}

export function setTokens(access: string, refresh?: string): void {
  localStorage.setItem(STORAGE_KEYS.access, access)
  if (refresh) localStorage.setItem(STORAGE_KEYS.refresh, refresh)
}

export function clearTokens(): void {
  localStorage.removeItem(STORAGE_KEYS.access)
  localStorage.removeItem(STORAGE_KEYS.refresh)
}

export function hasTokens(): boolean {
  return Boolean(getAccessToken())
}
