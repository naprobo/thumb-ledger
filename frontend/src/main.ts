import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import { i18n, getInitialLocale, setLocale } from './i18n'

// 创建并挂载应用
const app = createApp(App)

setLocale(getInitialLocale(), false)

app.use(createPinia())
app.use(router)
app.use(i18n)

app.mount('#app')
