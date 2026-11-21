// Money is stored in whole rupees by the API (`*_inr` fields).
const inr = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 });

export function formatINR(value) {
  if (value == null || Number.isNaN(Number(value))) return '—';
  return inr.format(Number(value));
}

// Compact form for axes and tiles: ₹950, ₹12.4k, ₹3.2L (lakh), ₹1.1Cr (crore).
export function formatINRCompact(value) {
  if (value == null || Number.isNaN(Number(value))) return '—';
  const v = Number(value);
  const abs = Math.abs(v);
  if (abs >= 1e7) return `₹${(v / 1e7).toFixed(1)}Cr`;
  if (abs >= 1e5) return `₹${(v / 1e5).toFixed(1)}L`;
  if (abs >= 1e3) return `₹${(v / 1e3).toFixed(1)}k`;
  return `₹${Math.round(v)}`;
}
