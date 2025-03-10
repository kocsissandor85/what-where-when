/**
 * Utility class for date operations
 */
export class DateUtils {
  /**
   * Format a date string for display
   * @param {string} dateStr - ISO date string
   * @returns {string} - Formatted date string
   */
  formatDate(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  }

  /**
   * Get the earliest date from an event's dates
   * @param {Object} event - Event object with dates array
   * @returns {string|null} - ISO date string or null
   */
  getEventFirstDate(event) {
    if (!event.dates || event.dates.length === 0) {
      return null;
    }

    // Sort dates chronologically
    const sortedDates = [...event.dates].sort((a, b) => {
      return new Date(a.date) - new Date(b.date);
    });

    return sortedDates[0].date;
  }

  /**
   * Get a date range formatted as a string
   * @param {Date} startDate - Start date
   * @param {Date} endDate - End date
   * @returns {string} - Formatted date range
   */
  formatDateRange(startDate, endDate) {
    if (!startDate || !endDate) return '';

    const formatOptions = { year: 'numeric', month: 'short', day: 'numeric' };
    const startStr = startDate.toLocaleDateString(undefined, formatOptions);
    const endStr = endDate.toLocaleDateString(undefined, formatOptions);

    return `${startStr} to ${endStr}`;
  }

  /**
   * Check if a date is in the past
   * @param {string|Date} date - Date to check
   * @returns {boolean} - True if date is in the past
   */
  isPastDate(date) {
    if (!date) return false;

    const checkDate = date instanceof Date ? date : new Date(date);
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    return checkDate < today;
  }

  /**
   * Get the current date as an ISO string (YYYY-MM-DD)
   * @returns {string} - Current date
   */
  getCurrentDateISO() {
    return new Date().toISOString().split('T')[0];
  }

  /**
   * Add days to a date
   * @param {Date} date - Starting date
   * @param {number} days - Number of days to add
   * @returns {Date} - New date
   */
  addDays(date, days) {
    const result = new Date(date);
    result.setDate(result.getDate() + days);
    return result;
  }

  /**
   * Get start and end of month containing the given date
   * @param {Date} date - Date within the month
   * @returns {Object} - Object with startOfMonth and endOfMonth properties
   */
  getMonthRange(date) {
    const startOfMonth = new Date(date.getFullYear(), date.getMonth(), 1);
    const endOfMonth = new Date(date.getFullYear(), date.getMonth() + 1, 0);

    return {
      startOfMonth,
      endOfMonth
    };
  }
}