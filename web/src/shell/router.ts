/**
 * 门户外壳路由。
 *
 * 模块路由从 registry 自动汇总并挂到 MainLayout 之下，
 * 因此新增模块不需要改动本文件。
 */

import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

import { setUnauthorizedHandler } from '@/shared/api/http'
import { SITE_NAME } from '@/shared/config'

import { useAuthStore } from './auth'
import MainLayout from './layouts/MainLayout.vue'
import { modules } from './registry'

/** 汇总所有内嵌模块的路由 */
const moduleRoutes: RouteRecordRaw[] = modules
  .filter((item) => item.kind === 'internal' && item.routes?.length)
  .flatMap((item) =>
    (item.routes ?? []).map((route) => ({
      ...route,
      meta: { ...route.meta, moduleKey: item.key },
    })),
  )

/** 模块内用绝对路径书写更自然，挂到布局下时去掉开头的斜杠 */
function toChildRoute(route: RouteRecordRaw): RouteRecordRaw {
  return { ...route, path: route.path.replace(/^\//, '') }
}

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'login',
    component: () => import('./views/LoginView.vue'),
    meta: { public: true, title: '登录' },
  },
  {
    path: '/',
    component: MainLayout,
    children: [
      { path: '', redirect: { name: 'dashboard' } },
      ...moduleRoutes.map(toChildRoute),
      {
        path: 'account',
        name: 'account',
        component: () => import('./views/AccountView.vue'),
        meta: { title: '个人设置', moduleKey: 'shell' },
      },
      {
        path: 'forbidden',
        name: 'forbidden',
        component: () => import('./views/ForbiddenView.vue'),
        meta: { title: '无权访问', moduleKey: 'shell' },
      },
      {
        path: ':pathMatch(.*)*',
        name: 'not-found',
        component: () => import('./views/NotFoundView.vue'),
        meta: { public: true, title: '页面不存在', moduleKey: 'shell' },
      },
    ],
  },
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()

  // 1) 公开页面直接放行
  if (to.meta.public) {
    return true
  }

  // 2) 会话就绪性
  const ok = await auth.ensureSession()
  if (!ok) {
    return {
      name: 'login',
      query: to.fullPath === '/' ? {} : { redirect: to.fullPath },
    }
  }

  // 3) 权限校验：路由自身声明的权限 与 所属模块声明的权限 都必须满足
  const routePerms = (to.meta.permissions as string[] | undefined) ?? []
  if (routePerms.length && !routePerms.every((code) => auth.hasPerm(code))) {
    return { name: 'forbidden' }
  }

  const moduleKey = to.meta.moduleKey as string | undefined
  const moduleItem = moduleKey ? modules.find((item) => item.key === moduleKey) : undefined
  if (moduleItem?.permission && !auth.hasPerm(moduleItem.permission)) {
    return { name: 'forbidden' }
  }

  return true
})

router.afterEach((to) => {
  const title = to.meta.title as string | undefined
  document.title = title ? `${title} · ${SITE_NAME}` : SITE_NAME
})

// 会话彻底失效（refresh 也失败）时回到登录页
setUnauthorizedHandler(() => {
  const auth = useAuthStore()
  const redirect = router.currentRoute.value.fullPath
  auth.reset()
  void router.replace({
    name: 'login',
    query: redirect && redirect !== '/' ? { redirect } : {},
  })
})
