/** 工作台模块。 */

import type { ModuleDescriptor } from '@/shell/types'

export default {
  key: 'dashboard',
  title: '工作台',
  icon: 'dashboard',
  kind: 'internal',
  path: '/dashboard',
  permission: 'portal.view',
  order: 10,
  description: '总览与快捷入口',
  routes: [
    {
      path: '/dashboard',
      name: 'dashboard',
      component: () => import('./views/DashboardView.vue'),
      meta: { title: '工作台', permissions: ['portal.view'] },
    },
  ],
} satisfies ModuleDescriptor
