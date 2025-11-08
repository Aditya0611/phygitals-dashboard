import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatPrice(price: string): number {
  const parsed = parsePriceValue(price)
  return parsed ?? 0
}

export function formatDate(date: string): string {
  return new Date(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

export function parsePriceValue(price: unknown): number | null {
  if (price === null || price === undefined) return null

  const numeric = String(price).replace(/[^0-9.-]/g, '').trim()
  if (!numeric || numeric === '-' || numeric === '.' || numeric === '-.' || numeric === '-0') {
    return null
  }

  const parsed = Number.parseFloat(numeric)
  return Number.isFinite(parsed) ? parsed : null
}

export function formatCurrency(
  price: unknown,
  {
    fallback = 'N/A',
    minimumFractionDigits = 2,
    maximumFractionDigits = 2
  }: { fallback?: string; minimumFractionDigits?: number; maximumFractionDigits?: number } = {}
): string {
  const parsed = parsePriceValue(price)
  if (parsed === null) return fallback

  return parsed.toLocaleString('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits,
    maximumFractionDigits
  })
}
