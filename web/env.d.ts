/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'

  const component: DefineComponent<Record<string, unknown>, Record<string, unknown>, unknown>
  export default component
}

interface ImportMetaEnv {
  /** 开发环境后端地址（仅 Vite 代理使用，浏览器不会读到） */
  readonly VITE_DEV_BACKEND?: string
  /** 站点名称，显示在标题与登录页 */
  readonly VITE_SITE_NAME?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
