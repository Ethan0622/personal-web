/**
 * ★ 模块注册中心 —— 门户的"总目录"。
 *
 * 这是整个门户可扩展性的关键：新增一个平台只需要在这里加一行。
 * 菜单渲染、路由注册、权限过滤全部自动生效，不需要改动任何其他代码。
 *
 * 两种模块类型：
 *   - internal：站内子应用，有自己的路由与页面（如考试平台）
 *   - external：第三方平台，只登记一个入口（如学校 OA）
 * 二者共用同一套结构，所以渲染逻辑只需要写一遍。
 */

import dashboardModule from '@/modules/dashboard'
import linksModule from '@/modules/links'

import type { ModuleDescriptor } from './types'

export const modules: ModuleDescriptor[] = [
  dashboardModule,
  linksModule,

  // ──────────────────────────────────────────────────────────────
  // 新增模块示例（迁移考试模块时取消注释即可）：
  //
  // {
  //   key: 'exam',
  //   title: '考试平台',
  //   icon: 'assignment',
  //   kind: 'internal',
  //   path: '/exam',
  //   permission: 'exam.view',
  //   routes: examRoutes,
  //   order: 30,
  //   description: '自适应在线考试与题库管理',
  // },
  //
  // ──────────────────────────────────────────────────────────────
  // 新增第三方平台入口示例：
  //
  // {
  //   key: 'school-oa',
  //   title: '学校 OA',
  //   icon: 'business',
  //   kind: 'external',
  //   path: 'https://oa.example.edu.cn',
  //   order: 90,
  // },
  // ──────────────────────────────────────────────────────────────
]

/** 按 order 排序后的全部模块 */
export const sortedModules: ModuleDescriptor[] = [...modules].sort((a, b) => a.order - b.order)
