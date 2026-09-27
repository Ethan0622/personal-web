import { createPinia } from 'pinia'
import { Dialog, Loading, Notify, Quasar } from 'quasar'
import quasarLang from 'quasar/lang/zh-CN'
import { createApp } from 'vue'

import '@quasar/extras/material-icons/material-icons.css'
import 'quasar/src/css/index.sass'
import '@/styles/main.scss'

import App from './App.vue'
import { router } from './shell/router'

const app = createApp(App)

// 注意顺序：pinia 必须先于 router 安装，
// 否则路由守卫里的 useAuthStore() 找不到活动的 pinia 实例。
app.use(createPinia())
app.use(router)

app.use(Quasar, {
  plugins: { Notify, Dialog, Loading },
  lang: quasarLang,
  config: {
    notify: { position: 'top', timeout: 3000 },
  },
})

app.mount('#app')
