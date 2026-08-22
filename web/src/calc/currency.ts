// Static exchange-rate snapshot (base = CNY), taken from cache/exchange_rates.json (dated 2025-09-25).
// This is a client-side fallback — no live API calls are made, matching the MVP scope for this page.

export const EXCHANGE_RATES_BASE = 'CNY'
export const EXCHANGE_RATES_DATE = '2025-09-25'

export const EXCHANGE_RATES: Record<string, number> = {
  CNY: 1,
  AUD: 0.213,
  BRL: 0.742,
  CAD: 0.195,
  CHF: 0.111,
  DKK: 0.89,
  EUR: 0.119,
  GBP: 0.104,
  HKD: 1.09,
  INR: 12.45,
  JPY: 20.83,
  KRW: 196.4,
  NOK: 1.39,
  RUB: 11.74,
  SEK: 1.32,
  SGD: 0.181,
  TWD: 4.26,
  USD: 0.14,
}

export const CURRENCY_NAMES: Record<string, string> = {
  CNY: '人民币',
  USD: '美元',
  SGD: '新加坡元',
  TWD: '新台币',
  JPY: '日元',
  EUR: '欧元',
  GBP: '英镑',
  HKD: '港币',
  KRW: '韩元',
  CAD: '加拿大元',
  AUD: '澳大利亚元',
}

const CURRENCY_SYMBOLS: Record<string, string> = {
  CNY: '¥',
  USD: '$',
  SGD: 'S$',
  TWD: 'NT$',
  JPY: '¥',
  EUR: '€',
  GBP: '£',
  HKD: 'HK$',
  KRW: '₩',
  CAD: 'C$',
  AUD: 'A$',
}

export function convertAmount(amount: number, fromCurrency: string, toCurrency: string): number {
  if (fromCurrency === toCurrency) return amount
  const cnyAmount = amount / (EXCHANGE_RATES[fromCurrency] ?? 1)
  return cnyAmount * (EXCHANGE_RATES[toCurrency] ?? 1)
}

export function formatCurrency(amount: number, currency: string): string {
  const symbol = CURRENCY_SYMBOLS[currency] ?? currency
  return `${symbol}${amount.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}
