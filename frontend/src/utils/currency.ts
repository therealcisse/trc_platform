/**
 * Currency formatting utilities
 * Default currency: EUR (Euro)
 */

export const formatCurrency = (cents: number): string => {
  return new Intl.NumberFormat('en-EU', {
    style: 'currency',
    currency: 'EUR',
  }).format(cents / 100);
};

export const formatNumber = (num: number): string => {
  return new Intl.NumberFormat('en-EU').format(num);
};

export const formatBytes = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// Currency symbol for display
export const CURRENCY_SYMBOL = '€';
export const CURRENCY_CODE = 'EUR';
