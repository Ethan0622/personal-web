/** 模块可见性计算：菜单、工作台卡片都走这里，保证口径一致。 */

import { computed } from 'vue'

import { modules, sortedModules } from './registry'
import { useAuthStore } from './auth'
import type { ModuleDescriptor } from './types'

export function useModules() {
  const auth = useAuthStore()

  /** 当前用户有权访问、且需要显示在菜单里的模块 */
  const visibleModules = computed<ModuleDescriptor[]>(() =>
    sortedModules.filter((item) => {
      if (item.hidden) return false
      if (!item.permission) return true
      return auth.hasAnyPerm([item.permission])
    }),
  )

  /** 工作台卡片用的模块（排除工作台自身与纯外链） */
  const dashboardCards = computed<ModuleDescriptor[]>(() =>
    visibleModules.value.filter((item) => item.key !== 'dashboard' && item.kind === 'internal'),
  )

  const externalModules = computed<ModuleDescriptor[]>(() =>
    visibleModules.value.filter((item) => item.kind === 'external'),
  )

  return { allModules: modules, visibleModules, dashboardCards, externalModules }
}
