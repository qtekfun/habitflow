import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'
import { format, isToday as dateFnsIsToday, parseISO } from 'date-fns'

/** Merge Tailwind class names, resolving conflicts. */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs))
}

/**
 * Format a streak count as a human-readable string.
 * Returns empty string for 0, "🔥 N day streak" for N > 0.
 */
export function formatStreak(n: number): string {
  if (n === 0) return ''
  return `🔥 ${n} day streak`
}

/**
 * Format an ISO date string (YYYY-MM-DD) as "Mon, Apr 7".
 */
export function formatDate(isoDate: string): string {
  return format(parseISO(isoDate), 'EEE, MMM d')
}

/**
 * Returns true if the given ISO date string (YYYY-MM-DD) is today.
 */
export function isToday(isoDate: string): boolean {
  return dateFnsIsToday(parseISO(isoDate))
}
