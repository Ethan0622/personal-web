/** 外链入口模块。 */

import type { ModuleDescriptor } from '@/shell/types'

export default {
  key: 'links',
  title: '外链入口',
  icon: 'link',
  kind: 'internal',
  path: '/links',
  permission: 'portal.links.view',
  order: 20,
  description: '通往其他平台的入口',
  routes: [
    {
      path: '/links',
      name: 'links',
      component: () => import('./views/LinksView.vue'),
      meta: { title: '外链入口', permissions: ['portal.links.view'] },
    },
  ],
} satisfies ModuleDescriptor
