import { fileURLToPath, URL } from 'node:url'

import { quasar, transformAssetUrls } from '@quasar/vite-plugin'
import vue from '@vitejs/plugin-vue'
import { defineConfig, loadEnv } from 'vite'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')

  // 必须用绝对路径：@quasar/vite-plugin 会把它拼成 @import 语句，
  // 若给相对路径，sass 会以 quasar 自身目录为基准解析而找不到文件。
  const quasarSassVariables = fileURLToPath(
    new URL('./src/styles/quasar.variables.scss', import.meta.url),
  )

  return {
    plugins: [
      vue({ template: { transformAssetUrls } }),
      quasar({ sassVariables: quasarSassVariables }),
    ],

    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },

    server: {
      host: true, // 允许局域网访问，方便真机调试
      port: 5173,
      proxy: {
        // 开发环境把 /api 代理到 Django，彻底绕开跨域问题
        '/api': {
          target: env.VITE_DEV_BACKEND || 'http://127.0.0.1:8000',
          changeOrigin: true,
        },
        '/media': {
          target: env.VITE_DEV_BACKEND || 'http://127.0.0.1:8000',
          changeOrigin: true,
        },
      },
    },

    build: {
      outDir: 'dist',
      sourcemap: false,
      // 服务器只有 3M 带宽，首屏体积需要关注
      chunkSizeWarningLimit: 800,
      // 分包策略交给 Vite 默认处理。
      //
      // 注意：Vite 8 底层打包器已从 Rollup 换成 Rolldown，旧的
      // output.manualChunks 属于废弃 API —— 实测它会被部分忽略：
      // Vue 运行时被打进业务模块 chunk，反而让 module-links 反向依赖
      // module-dashboard。因此不再手工指定，依赖默认按需拆分：
      //   · 各模块页面本身是动态 import，天然独立成 chunk
      //   · 共享依赖由打包器自动归并到公共 chunk
    },
  }
})
