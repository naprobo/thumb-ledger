import { describe, expect, it, beforeEach } from 'vitest'

import { getInitialLocale, i18n, setLocale, SUPPORTED_LOCALES } from '@/i18n'
import { translateLabel } from '@/i18n/labels'

describe('i18n infrastructure', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('uses saved supported locale before browser fallback', () => {
    localStorage.setItem('preferred_language', 'ja')

    expect(getInitialLocale()).toBe('ja')
  })

  it('falls back when saved locale is unsupported', () => {
    localStorage.setItem('preferred_language', 'fr')

    expect(SUPPORTED_LOCALES).toContain(getInitialLocale())
  })

  it('persists locale changes locally', () => {
    setLocale('en')

    expect(localStorage.getItem('preferred_language')).toBe('en')
    expect(document.documentElement.lang).toBe('en')
  })

  it('updates translated message keys immediately when locale changes', () => {
    setLocale('zh-CN')
    expect(i18n.global.t('auth.login')).toBe('登录')

    setLocale('ja')
    expect(i18n.global.t('auth.login')).toBe('ログイン')

    setLocale('en')
    expect(i18n.global.t('auth.login')).toBe('Login')
  })

  it('translates built-in category and item keys instead of showing raw keys', () => {
    setLocale('zh-CN')
    const t = i18n.global.t

    expect(translateLabel('category.food', t)).toBe('食品饮料')
    expect(translateLabel('category.vehicle', t)).toBe('汽车用车')
    expect(translateLabel('category.housing', t)).toBe('居住')
    expect(translateLabel('item.rent', t)).toBe('房租')
    expect(translateLabel('item.mortgage', t)).toBe('房贷')
    expect(translateLabel('category.housing', t)).not.toBe('category.housing')
  })
})
