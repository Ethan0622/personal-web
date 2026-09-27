/** 门户外壳的认证状态。 */

import { defineStore } from 'pinia'

import { api } from '@/shared/api/http'
import { clearTokens, getRefreshToken, hasTokens, setTokens } from '@/shared/api/tokens'
import type { LoginResult, PortalUser } from '@/shared/types'

interface State {
  user: PortalUser | null
  /** 是否已经尝试过恢复会话，避免路由守卫反复请求 */
  initialized: boolean
  loading: boolean
}

export const useAuthStore = defineStore('auth', {
  state: (): State => ({
    user: null,
    initialized: false,
    loading: false,
  }),

  getters: {
    isLoggedIn: (state): boolean => Boolean(state.user),
    displayName: (state): string => state.user?.real_name || state.user?.username || '',
    roleLabel: (state): string => state.user?.role_display ?? '',
  },

  actions: {
    /** 是否持有某个权限码。超管持有通配符 "*"，恒为真。 */
    hasPerm(code: string): boolean {
      const perms = this.user?.perms
      if (!perms) return false
      return perms.includes('*') || perms.includes(code)
    },

    /** 是否持有其中任意一个权限码 */
    hasAnyPerm(codes: string[]): boolean {
      if (!codes.length) return true
      return codes.some((code) => this.hasPerm(code))
    },

    async login(username: string, password: string): Promise<PortalUser> {
      this.loading = true
      try {
        const data = await api.post<LoginResult>('/api/core/auth/login/', { username, password })
        setTokens(data.access, data.refresh)
        this.user = data.user
        this.initialized = true
        return data.user
      } finally {
        this.loading = false
      }
    },

    /** 拉取当前用户；token 无效或过期则清空会话。 */
    async fetchMe(): Promise<PortalUser | null> {
      if (!hasTokens()) {
        this.initialized = true
        return null
      }
      try {
        this.user = await api.get<PortalUser>('/api/core/auth/me/')
      } catch {
        this.user = null
        clearTokens()
      } finally {
        this.initialized = true
      }
      return this.user
    },

    /** 确保会话已就绪（路由守卫用） */
    async ensureSession(): Promise<boolean> {
      if (this.user) return true
      if (!hasTokens()) {
        this.initialized = true
        return false
      }
      if (!this.initialized) {
        await this.fetchMe()
      }
      return Boolean(this.user)
    },

    async updateProfile(payload: Partial<Pick<PortalUser, 'real_name' | 'email' | 'phone'>>) {
      this.user = await api.patch<PortalUser>('/api/core/auth/me/', payload)
      return this.user
    },

    async changePassword(oldPassword: string, newPassword: string): Promise<void> {
      await api.post('/api/core/auth/change-password/', {
        old_password: oldPassword,
        new_password: newPassword,
      })
    },

    async logout(): Promise<void> {
      const refresh = getRefreshToken()
      try {
        if (refresh) {
          await api.post('/api/core/auth/logout/', { refresh })
        }
      } catch {
        // 登出接口失败不应阻塞本地清理
      } finally {
        clearTokens()
        this.user = null
        this.initialized = true
      }
    },

    /** 会话失效（由 http 层回调触发） */
    reset(): void {
      clearTokens()
      this.user = null
      this.initialized = true
    },
  },
})
