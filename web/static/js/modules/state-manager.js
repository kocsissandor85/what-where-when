/**
 * Manages application state
 */
export class StateManager {
  constructor() {
    this.events = [];
    this.filter = '';
    this.sortBy = 'title';
    this.sortDir = 'asc';
    this.includeArchived = false;
    this.dateRangeStart = null;
    this.dateRangeEnd = null;
  }

  /**
   * Set the current list of events
   * @param {Array} events - Event objects
   */
  setEvents(events) {
    this.events = events;
  }

  /**
   * Get the current list of events
   * @returns {Array} - Event objects
   */
  getEvents() {
    return this.events;
  }

  /**
   * Remove an event from the state
   * @param {number} eventId - ID of the event to remove
   */
  removeEvent(eventId) {
    this.events = this.events.filter(event => event.id != eventId);
  }

  /**
   * Set the current filter text
   * @param {string} filter - Filter text
   */
  setFilter(filter) {
    this.filter = filter;
  }

  /**
   * Get the current filter text
   * @returns {string} - Filter text
   */
  getFilter() {
    return this.filter;
  }

  /**
   * Set the sort column
   * @param {string} sortBy - Column to sort by
   */
  setSortBy(sortBy) {
    this.sortBy = sortBy;
  }

  /**
   * Get the current sort column
   * @returns {string} - Column being sorted
   */
  getSortBy() {
    return this.sortBy;
  }

  /**
   * Set the sort direction
   * @param {string} direction - 'asc' or 'desc'
   */
  setSortDirection(direction) {
    this.sortDir = direction;
  }

  /**
   * Get the current sort direction
   * @returns {string} - 'asc' or 'desc'
   */
  getSortDirection() {
    return this.sortDir;
  }

  /**
   * Toggle the sort direction between 'asc' and 'desc'
   */
  toggleSortDirection() {
    this.sortDir = this.sortDir === 'asc' ? 'desc' : 'asc';
  }

  /**
   * Set whether to include archived events
   * @param {boolean} include - Whether to include archived events
   */
  setIncludeArchived(include) {
    this.includeArchived = include;
  }

  /**
   * Get whether archived events are included
   * @returns {boolean} - Whether archived events are included
   */
  getIncludeArchived() {
    return this.includeArchived;
  }

  /**
   * Set the date range for filtering
   * @param {Date} startDate - Start date
   * @param {Date} endDate - End date
   */
  setDateRange(startDate, endDate) {
    this.dateRangeStart = startDate;
    this.dateRangeEnd = endDate;
  }

  /**
   * Clear the date range filter
   */
  clearDateRange() {
    this.dateRangeStart = null;
    this.dateRangeEnd = null;
  }

  /**
   * Get a filter by type
   * @param {string} type - Filter type ('text', 'date', 'archived')
   */
  clearFilterByType(type) {
    switch (type) {
      case 'text':
        this.filter = '';
        break;
      case 'date':
        this.clearDateRange();
        break;
      case 'archived':
        this.includeArchived = false;
        break;
    }
  }

  /**
   * Get all current filters for UI display
   * @returns {Object} - Filters object
   */
  getFiltersForDisplay() {
    return {
      text: this.filter,
      dateStart: this.dateRangeStart,
      dateEnd: this.dateRangeEnd,
      includeArchived: this.includeArchived
    };
  }

  /**
   * Get query parameters for API requests
   * @returns {Object} - Parameters object
   */
  getQueryParams() {
    const params = {
      filter: this.filter,
      sort_by: this.sortBy,
      sort_dir: this.sortDir,
      include_archived: this.includeArchived
    };

    // Add date range if set
    if (this.dateRangeStart && this.dateRangeEnd) {
      params.date_start = this.dateRangeStart.toISOString().split('T')[0];
      params.date_end = this.dateRangeEnd.toISOString().split('T')[0];
    }

    return params;
  }
}