/**
 * 门户外壳的类型定义。
 *
 * 单独成文件是为了避免循环引用：registry 需要引入各模块，
 * 各模块又需要 ModuleDescriptor 类型 —— 类型放这里，两边都只依赖它。
 */

import type { RouteRecordRaw } from 'vue-router'

export type ModuleKind = 'internal' | 'external'

/**
 * 模块描述符 —— 门户的"总目录"条目。
 *
 * 新增一个平台/模块时，只需要：
 *   1. 内嵌模块：在 src/modules/<key>/ 下实现页面，导出本结构，再到 registry.ts 注册一行
 *   2. 外链平台：把 kind 设为 'external'，path 填第三方地址
 * 菜单、路由、权限会自动生效。
 */
export interface ModuleDescriptor {
  /** 唯一标识，如 'dashboard'、'exam' */
  key: string
  /** 显示名称 */
  title: string
  /** Quasar 图标名 */
  icon: string
  /** internal = 站内子应用；external = 跳转第三方平台 */
  kind: ModuleKind
  /** internal 时为路由前缀；external 时为完整地址 */
  path: string
  /**
   * 访问所需权限码。**必须显式声明** —— 未声明则仅登录可见，
   * 这是"默认拒绝"原则在模块层的体现。
   */
  permission?: string
  /** 内嵌模块自己的路由 */
  routes?: RouteRecordRaw[]
  /** 菜单排序，数字小的在前 */
  order: number
  /** 模块简介，显示在工作台卡片上 */
  description?: string
  /** 不在菜单中显示（如系统级页面） */
  hidden?: boolean
}
