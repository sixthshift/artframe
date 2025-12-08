/**
 * Tests for date formatting utilities.
 */

import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import { formatDateTime, formatDate, formatTime, formatRelativeTime } from './date'

describe('formatDateTime', () => {
  it('should format a Date object to full datetime string', () => {
    const date = new Date('2025-12-03T23:01:28Z')
    const result = formatDateTime(date)
    // sv-SE locale produces ISO-like format
    expect(result).toMatch(/2025-12-0[34]/)
    expect(result).toMatch(/\d{2}:\d{2}:\d{2}/)
  })

  it('should format an ISO string to full datetime string', () => {
    const result = formatDateTime('2025-12-03T23:01:28Z')
    expect(result).toMatch(/2025-12-0[34]/)
    expect(result).toMatch(/\d{2}:\d{2}:\d{2}/)
  })

  it('should return empty string for null', () => {
    expect(formatDateTime(null)).toBe('')
  })

  it('should return empty string for undefined', () => {
    expect(formatDateTime(undefined)).toBe('')
  })

  it('should return empty string for invalid date string', () => {
    expect(formatDateTime('invalid-date')).toBe('')
  })

  it('should return empty string for empty string', () => {
    expect(formatDateTime('')).toBe('')
  })
})

describe('formatDate', () => {
  it('should format a Date object to date only string', () => {
    const date = new Date('2025-12-03T23:01:28Z')
    const result = formatDate(date)
    expect(result).toMatch(/2025-12-0[34]/)
    // Should not include time
    expect(result).not.toMatch(/\d{2}:\d{2}:\d{2}/)
  })

  it('should format an ISO string to date only string', () => {
    const result = formatDate('2025-06-15T10:30:00Z')
    expect(result).toMatch(/2025-06-15/)
  })

  it('should return empty string for null', () => {
    expect(formatDate(null)).toBe('')
  })

  it('should return empty string for undefined', () => {
    expect(formatDate(undefined)).toBe('')
  })

  it('should return empty string for invalid date string', () => {
    expect(formatDate('not-a-date')).toBe('')
  })
})

describe('formatTime', () => {
  it('should format a Date object to time only string', () => {
    const date = new Date('2025-12-03T23:01:28Z')
    const result = formatTime(date)
    expect(result).toMatch(/\d{2}:\d{2}:\d{2}/)
    // Should not include date
    expect(result).not.toMatch(/2025/)
  })

  it('should format an ISO string to time only string', () => {
    const result = formatTime('2025-06-15T10:30:45Z')
    expect(result).toMatch(/\d{2}:\d{2}:\d{2}/)
  })

  it('should return empty string for null', () => {
    expect(formatTime(null)).toBe('')
  })

  it('should return empty string for undefined', () => {
    expect(formatTime(undefined)).toBe('')
  })

  it('should return empty string for invalid date string', () => {
    expect(formatTime('invalid')).toBe('')
  })
})

describe('formatRelativeTime', () => {
  beforeEach(() => {
    // Mock current time to a fixed point
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2025-01-15T12:00:00Z'))
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('should format a date in the past as "X ago"', () => {
    const result = formatRelativeTime('2025-01-15T11:55:00Z')
    expect(result).toMatch(/5 minutes ago|in -5 minutes/)
  })

  it('should format a date in the future as "in X"', () => {
    const result = formatRelativeTime('2025-01-15T13:00:00Z')
    expect(result).toMatch(/in 1 hour|1 hour/)
  })

  it('should format seconds when within a minute', () => {
    const result = formatRelativeTime('2025-01-15T11:59:30Z')
    expect(result).toMatch(/second/)
  })

  it('should format days when more than 24 hours', () => {
    const result = formatRelativeTime('2025-01-13T12:00:00Z')
    expect(result).toMatch(/day/)
  })

  it('should return empty string for null', () => {
    expect(formatRelativeTime(null)).toBe('')
  })

  it('should return empty string for undefined', () => {
    expect(formatRelativeTime(undefined)).toBe('')
  })

  it('should return empty string for invalid date string', () => {
    expect(formatRelativeTime('invalid')).toBe('')
  })

  it('should accept Date objects', () => {
    const date = new Date('2025-01-15T11:30:00Z')
    const result = formatRelativeTime(date)
    expect(result).toMatch(/30 minutes ago|in -30 minutes/)
  })
})
