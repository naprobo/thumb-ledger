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
  if (!symbol) return `${amount.toLocaleString()} ${currencyCode}`
  return `${symbol}${amount.toLocaleString()}`
}

export function getCurrencySymbol(currencyCode: string): string {
  return CURRENCY_SYMBOLS[currencyCode.toUpperCase()] || currencyCode
}
