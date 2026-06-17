// Vitest 测试环境初始化
import { config } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach } from 'vitest'
import { messages } from '@/i18n'

// 全局配置 i18n
const i18n = createI18n({
  legacy: false,
  locale: 'zh-CN',
  fallbackLocale: 'zh-CN',
  messages,
})

config.global.plugins = [i18n]

// 每个测试前重置 Pinia
beforeEach(() => {
  setActivePinia(createPinia())
})
