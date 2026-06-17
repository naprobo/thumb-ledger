import { createI18n } from 'vue-i18n'

import zhCN from './zh-CN'
import en from './en'
import ja from './ja'

export type SupportedLocale = 'zh-CN' | 'en' | 'ja'

export const SUPPORTED_LOCALES: SupportedLocale[] = ['zh-CN', 'en', 'ja']

export const messages = {
  'zh-CN': zhCN,
  en,
  ja,
}

/**
 * 根据浏览器语言偏好返回支持的语言代码
 * 如果浏览器语言不在支持列表中，默认返回 zh-CN
 */
export function getBrowserLocale(): SupportedLocale {
  const browserLang = navigator.language || 'zh-CN'

  // 精确匹配
  if (SUPPORTED_LOCALES.includes(browserLang as SupportedLocale)) {
    return browserLang as SupportedLocale
  }

  // 前缀匹配（如 zh-TW → zh-CN，en-US → en）
  const prefix = browserLang.split('-')[0]
  if (prefix === 'zh') return 'zh-CN'
  if (prefix === 'en') return 'en'
  if (prefix === 'ja') return 'ja'

  return 'zh-CN'
}

export function getInitialLocale(): SupportedLocale {
  const savedLocale = localStorage.getItem('preferred_language')
  if (SUPPORTED_LOCALES.includes(savedLocale as SupportedLocale)) {
    return savedLocale as SupportedLocale
  }
  return getBrowserLocale()
}

export const i18n = createI18n({
  legacy: false,
  locale: getInitialLocale(),
  fallbackLocale: 'zh-CN',
  messages,
})

export function setLocale(locale: SupportedLocale, persist = true): void {
  i18n.global.locale.value = locale
  if (persist) {
    localStorage.setItem('preferred_language', locale)
  }
  document.documentElement.lang = locale
}
