/**
 * Utility functions for the ChatBet application.
 */

/**
 * Generate a simple UUID v4
 */
export function generateUUID(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

/**
 * Format date for display
 */
export function formatDate(date: Date, format: 'short' | 'long' | 'time' = 'short'): string {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (format === 'time') {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  if (diffMins < 1) {
    return 'Just now';
  } else if (diffMins < 60) {
    return `${diffMins}m ago`;
  } else if (diffHours < 24) {
    return `${diffHours}h ago`;
  } else if (diffDays < 7) {
    return `${diffDays}d ago`;
  } else {
    return date.toLocaleDateString();
  }
}

/**
 * Truncate text to specified length
 */
export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) {
    return text;
  }
  return text.substring(0, maxLength - 3) + '...';
}

/**
 * Debounce function
 */
export function debounce<T extends (...args: unknown[]) => unknown>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: ReturnType<typeof setTimeout>;

  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}

/**
 * Throttle function
 */
export function throttle<T extends (...args: unknown[]) => unknown>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle: boolean;

  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
}

/**
 * Format currency
 */
export function formatCurrency(amount: number, currency = 'EUR'): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency
  }).format(amount);
}

/**
 * Format odds
 */
export function formatOdds(odds: number, format: 'decimal' | 'fractional' | 'american' = 'decimal'): string {
  switch (format) {
    case 'decimal':
      return odds.toFixed(2);
    case 'fractional':
      const decimal = odds - 1;
      const gcd = (a: number, b: number): number => b === 0 ? a : gcd(b, a % b);
      const numerator = Math.round(decimal * 100);
      const denominator = 100;
      const divisor = gcd(numerator, denominator);
      return `${numerator / divisor}/${denominator / divisor}`;
    case 'american':
      if (odds >= 2) {
        return `+${Math.round((odds - 1) * 100)}`;
      } else {
        return `-${Math.round(100 / (odds - 1))}`;
      }
    default:
      return odds.toFixed(2);
  }
}

/**
 * Validate email format
 */
export function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/**
 * Generate a random color for user avatars
 */
export function generateAvatarColor(text: string): string {
  const colors = [
    '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
    '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9'
  ];

  let hash = 0;
  for (let i = 0; i < text.length; i++) {
    hash = text.charCodeAt(i) + ((hash << 5) - hash);
  }

  return colors[Math.abs(hash) % colors.length];
}

/**
 * Parse team names from message content
 */
export function parseTeamNames(content: string): string[] {
  // Simple regex to match potential team names (capitalized words)
  const teamPattern = /\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b/g;
  const matches = content.match(teamPattern) || [];

  // Filter out common words that aren't team names
  const commonWords = ['The', 'And', 'Or', 'But', 'When', 'Where', 'What', 'How', 'Why', 'Can', 'Will', 'Should'];
  return matches.filter(match => !commonWords.includes(match));
}

/**
 * Calculate confidence level from score
 */
export function getConfidenceLevel(score: number): 'high' | 'medium' | 'low' {
  if (score >= 0.8) return 'high';
  if (score >= 0.5) return 'medium';
  return 'low';
}

/**
 * Format file size for display
 */
export function formatFileSize(bytes: number): string {
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  if (bytes === 0) return '0 Bytes';

  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
}

/**
 * Check if device is mobile
 */
export function isMobile(): boolean {
  return window.innerWidth <= 768;
}

/**
 * Check if device is tablet
 */
export function isTablet(): boolean {
  return window.innerWidth > 768 && window.innerWidth <= 1024;
}

/**
 * Get browser information
 */
export function getBrowserInfo(): { name: string; version: string } {
  const userAgent = navigator.userAgent;

  if (userAgent.includes('Chrome')) {
    return { name: 'Chrome', version: userAgent.match(/Chrome\/(\d+)/)?.[1] || 'Unknown' };
  } else if (userAgent.includes('Firefox')) {
    return { name: 'Firefox', version: userAgent.match(/Firefox\/(\d+)/)?.[1] || 'Unknown' };
  } else if (userAgent.includes('Safari')) {
    return { name: 'Safari', version: userAgent.match(/Version\/(\d+)/)?.[1] || 'Unknown' };
  } else if (userAgent.includes('Edge')) {
    return { name: 'Edge', version: userAgent.match(/Edge\/(\d+)/)?.[1] || 'Unknown' };
  }

  return { name: 'Unknown', version: 'Unknown' };
}
