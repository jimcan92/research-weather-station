import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatTemp(c: number | string | null): string {
  if (c == null) return '—';
  return `${Number(c).toFixed(1)}°C`;
}

export function formatHumidity(h: number | string | null): string {
  if (h == null) return '—';
  return `${Number(h).toFixed(0)}%`;
}

export function formatPressure(hpa: number | string | null): string {
  if (hpa == null) return '—';
  return `${Number(hpa).toFixed(1)} hPa`;
}

export function formatVoltage(v: number | string | null): string {
  if (v == null) return '—';
  return `${Number(v).toFixed(2)}V`;
}

export function formatSpeed(ms: number | string | null): string {
  if (ms == null) return '—';
  return `${Number(ms).toFixed(1)} m/s`;
}

export function formatDate(d: string | Date | null): string {
  if (!d) return '—';
  return new Date(d).toLocaleString('en-PH', {
    month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit'
  });
}

export function batteryColor(v: number | null): string {
  if (v == null) return 'text-gray-400';
  if (v >= 3.8) return 'text-green-500';
  if (v >= 3.5) return 'text-yellow-500';
  return 'text-red-500';
}
