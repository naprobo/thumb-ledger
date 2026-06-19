const CURRENCY_SYMBOLS: Record<string, string> = {
  AED: 'د.إ',
  AUD: 'A$',
  BRL: 'R$',
  CAD: 'C$',
  CHF: 'CHF',
  CNY: '¥',
  CZK: 'Kč',
  DKK: 'kr',
  EUR: '€',
  GBP: '£',
  HKD: 'HK$',
  HUF: 'Ft',
  IDR: 'Rp',
  ILS: '₪',
  INR: '₹',
  JPY: '¥',
  KRW: '₩',
  MXN: 'Mex$',
  MYR: 'RM',
  NOK: 'kr',
  NZD: 'NZ$',
  PHP: '₱',
  PLN: 'zł',
  SAR: '﷼',
  SEK: 'kr',
  SGD: 'S$',
  THB: '฿',
  TRY: '₺',
  TWD: 'NT$',
  USD: '$',
  VND: '₫',
  ZAR: 'R',
}

export function formatMoney(amount: number, currencyCode: string): string {
  const code = currencyCode.toUpperCase()
  const symbol = getCurrencySymbol(code)
  const scale = currencyFractionDigits(code)
  const displayAmount = formatMinorUnitAmount(amount, scale)
  if (!symbol) return `${displayAmount} ${currencyCode}`
  return `${symbol}${displayAmount}`
}

export function getCurrencySymbol(currencyCode: string): string {
  return CURRENCY_SYMBOLS[currencyCode.toUpperCase()] || currencyCode
}

export function currencyFractionDigits(currencyCode: string): number {
  const zeroDecimalCurrencies = new Set(['BIF', 'CLP', 'DJF', 'GNF', 'ISK', 'JPY', 'KMF', 'KRW', 'PYG', 'RWF', 'UGX', 'VND', 'VUV', 'XAF', 'XOF', 'XPF'])
  return zeroDecimalCurrencies.has(currencyCode.toUpperCase()) ? 0 : 2
}

function formatMinorUnitAmount(amount: number, scale: number): string {
  if (scale === 0) return amount.toLocaleString()
  const divisor = 10 ** scale
  const sign = amount < 0 ? '-' : ''
  const absoluteAmount = Math.abs(amount)
  const whole = Math.floor(absoluteAmount / divisor)
  const minor = absoluteAmount % divisor
  if (minor === 0) return `${sign}${whole.toLocaleString()}`
  const fraction = String(minor).padStart(scale, '0')
  return `${sign}${whole.toLocaleString()}.${fraction}`
}
