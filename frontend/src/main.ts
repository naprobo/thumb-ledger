import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import { i18n, getInitialLocale, setLocale } from './i18n'
import { createAppVuetify } from './plugins/vuetify'

// 创建并挂载应用
const app = createApp(App)
const vuetify = createAppVuetify()

setLocale(getInitialLocale(), false)

app.use(createPinia())
app.use(router)
app.use(i18n)
app.use(vuetify)

app.mount('#app')
