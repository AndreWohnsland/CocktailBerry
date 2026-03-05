/**
 * Format an ISO date string (YYYY-MM-DD) according to the given locale.
 */
export function formatDate(dateStr: string, locale: string): string {
  const [year, month, day] = dateStr.split('-').map(Number);
  return new Date(year, month - 1, day).toLocaleDateString(locale, {
    weekday: 'short',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  });
}
