import { describe, expect, it } from 'vitest'

import { formatMoney } from '@/utils/money'

describe('formatMoney', () => {
  it('formats zero-decimal and minor-unit currencies with symbols', () => {
    expect(formatMoney(1200, 'JPY')).toBe('¥1,200')
    expect(formatMoney(9600, 'USD')).toBe('$96')
    expect(formatMoney(9650, 'USD')).toBe('$96.50')
    expect(formatMoney(1234, 'CNY')).toBe('¥12.34')
  })
})
