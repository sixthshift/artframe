/**
 * Date formatting utilities for consistent date/time display across the app.
 * Uses ISO 8601-like format (YYYY-MM-DD HH:MM:SS) for clarity.
 */

const DATE_TIME_OPTIONS: Intl.DateTimeFormatOptions = {
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit',
  second: '2-digit',
  hour12: false,
}

const DATE_OPTIONS: Intl.DateTimeFormatOptions = {
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
}

const TIME_OPTIONS: Intl.DateTimeFormatOptions = {
  hour: '2-digit',
  minute: '2-digit',
  second: '2-digit',
  hour12: false,
}

// sv-SE locale produces ISO 8601-like format: YYYY-MM-DD HH:MM:SS
const LOCALE = 'sv-SE'

/**
 * Format a date/time value to full datetime string.
 * Output: "2025-12-03 23:01:28"
 */
export function formatDateTime(value: string | Date | null | undefined): string {
  if (!value) return ''
  const date = typeof value === 'string' ? new Date(value) : value
  if (isNaN(date.getTime())) return ''
  return date.toLocaleString(LOCALE, DATE_TIME_OPTIONS)
}

/**
 * Format a date/time value to date only.
 * Output: "2025-12-03"
 */
export function formatDate(value: string | Date | null | undefined): string {
  if (!value) return ''
  const date = typeof value === 'string' ? new Date(value) : value
  if (isNaN(date.getTime())) return ''
  return date.toLocaleDateString(LOCALE, DATE_OPTIONS)
}

/**
 * Format a date/time value to time only.
 * Output: "23:01:28"
 */
export function formatTime(value: string | Date | null | undefined): string {
  if (!value) return ''
  const date = typeof value === 'string' ? new Date(value) : value
  if (isNaN(date.getTime())) return ''
  return date.toLocaleTimeString(LOCALE, TIME_OPTIONS)
}

/**
 * Format a relative time (e.g., "2 minutes ago", "in 5 hours").
 */
export function formatRelativeTime(value: string | Date | null | undefined): string {
  if (!value) return ''
  const date = typeof value === 'string' ? new Date(value) : value
  if (isNaN(date.getTime())) return ''

  const now = new Date()
  const diffMs = date.getTime() - now.getTime()
  const diffSeconds = Math.round(diffMs / 1000)
  const diffMinutes = Math.round(diffSeconds / 60)
  const diffHours = Math.round(diffMinutes / 60)
  const diffDays = Math.round(diffHours / 24)

  const rtf = new Intl.RelativeTimeFormat('en', { numeric: 'auto' })

  if (Math.abs(diffSeconds) < 60) {
    return rtf.format(diffSeconds, 'second')
  } else if (Math.abs(diffMinutes) < 60) {
    return rtf.format(diffMinutes, 'minute')
  } else if (Math.abs(diffHours) < 24) {
    return rtf.format(diffHours, 'hour')
  } else {
    return rtf.format(diffDays, 'day')
  }
}
