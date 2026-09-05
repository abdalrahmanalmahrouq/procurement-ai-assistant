export const formatCurrency = (value: number, maximumFractionDigits = 0) =>
  new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits,
  }).format(value);

export const formatCompactCurrency = (value: number) => {
  if (value >= 1_000_000_000) return `USD ${(value / 1_000_000_000).toFixed(2)}B`;
  if (value >= 1_000_000) return `USD ${(value / 1_000_000).toFixed(2)}M`;
  if (value >= 1_000) return `USD ${(value / 1_000).toFixed(1)}K`;
  return formatCurrency(value);
};

export const formatCompactNumber = (value: number) =>
  new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 1 }).format(value);
