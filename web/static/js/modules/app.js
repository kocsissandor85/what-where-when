import { EventAPI } from './api.js';
import { UIManager } from './ui-manager.js';
import { StateManager } from './state-manager.js';
import { DateUtils } from './date-utils.js';
import { TagManager } from './tag-manager.js';

/**
 * Main application controller class
 */
export class EventManagerApp {
  constructor() {
    // Create module instances
    this.api = new EventAPI();
    this.state = new StateManager();
    this.ui = new UIManager(this.handleUIEvents.bind(this));
    this.dateUtils = new DateUtils();
    this.tagManager = new TagManager(this.handleTagFilter.bind(this));
  }

  /**
   * Initialize the application
   */
  init() {
    // Initialize UI components
    this.ui.initializeDatePicker(this.handleDateChange.bind(this));

    // Set up event handlers
    this.setupEventListeners();

    // Load initial data
    this.fetchEvents();
  }

  /**
   * Set up event listeners for UI elements
   */
  setupEventListeners() {
    // Filter button
    this.ui.elements.filterButton.addEventListener('click', () => this.applyFilter());

    // Filter input
    this.ui.elements.filterInput.addEventListener('keyup', (event) => {
      if (event.key === 'Enter') {
        this.applyFilter();
      }
    });

    // Clear date button
    this.ui.elements.clearDateButton.addEventListener('click', () => {
      this.ui.clearDatePicker();
      this.state.clearDateRange();
      this.fetchEvents();
      this.updateFilterTags();
    });

    // Show archived checkbox
    this.ui.elements.showArchived.addEventListener('change', (event) => {
      this.state.setIncludeArchived(event.target.checked);
      this.fetchEvents();
      this.updateFilterTags();
    });

    // Select all checkbox
    this.ui.elements.selectAll.addEventListener('change', (event) => {
      this.ui.selectAllEvents(event.target.checked);
      this.updateActionButtons();
    });

    // Bulk delete button
    this.ui.elements.bulkDeleteButton.addEventListener('click', () => {
      const selectedIds = this.getSelectedEventIds();
      if (selectedIds.length > 0 && confirm(`Are you sure you want to delete ${selectedIds.length} events?`)) {
        this.bulkDeleteEvents(selectedIds);
      }
    });

    // Bulk archive button
    this.ui.elements.bulkArchiveButton.addEventListener('click', () => {
      const selectedIds = this.getSelectedEventIds();
      if (selectedIds.length > 0) {
        this.ui.showArchiveConfirmation(selectedIds.length);
      }
    });

    // Confirm archive button
    this.ui.elements.confirmArchiveButton.addEventListener('click', () => {
      const selectedIds = this.getSelectedEventIds();
      if (selectedIds.length > 0) {
        this.bulkArchiveEvents(selectedIds);
      }
    });

    // Export to calendar button
    this.ui.elements.exportCalendarButton.addEventListener('click', () => {
      const selectedIds = this.getSelectedEventIds();
      if (selectedIds.length > 0) {
        this.exportToCalendar(selectedIds);
      }
    });

    // Sortable column headers
    document.querySelectorAll('th[data-sort]').forEach(th => {
      th.addEventListener('click', () => {
        const sortBy = th.getAttribute('data-sort');
        this.toggleSortDirection(sortBy);
        this.fetchEvents();
      });
    });
  }

  /**
   * Handler for UI events from UIManager
   * @param {string} eventType - Type of event
   * @param {*} data - Event data
   */
  handleUIEvents(eventType, data) {
    switch (eventType) {
      case 'delete':
        this.deleteEvent(data);
        break;
      case 'archive':
        this.archiveEvent(data);
        break;
      case 'removeFilter':
        this.removeFilter(data);
        break;
    }
  }

  /**
   * Handler for date picker changes
   * @param {Array<Date>} selectedDates - Selected dates
   */
  handleDateChange(selectedDates) {
    if (selectedDates.length === 2) {
      this.state.setDateRange(selectedDates[0], selectedDates[1]);
      this.fetchEvents();
      this.updateFilterTags();
    }
  }

  /**
   * Apply text filter
   */
  applyFilter() {
    const filterText = this.ui.elements.filterInput.value.trim();
    this.state.setFilter(filterText);
    this.fetchEvents();
    this.updateFilterTags();
  }

  /**
   * Remove a filter by type
   * @param {string} filterType - Type of filter to remove
   */
  removeFilter(filterType) {
    this.state.clearFilterByType(filterType);

    // Update UI to match state
    if (filterType === 'text') {
      this.ui.elements.filterInput.value = '';
    } else if (filterType === 'date') {
      this.ui.clearDatePicker();
    } else if (filterType === 'archived') {
      this.ui.elements.showArchived.checked = false;
    } else if (filterType === 'tag') {
      // No UI element to reset for tag filter as it's a dropdown
    }

    // Refresh data and UI
    this.fetchEvents();
    this.updateFilterTags();
  }

  /**
   * Update filter tags in the UI
   */
  updateFilterTags() {
    const filters = this.state.getFiltersForDisplay();
    this.ui.updateFilterTags(filters);
  }

  /**
   * Toggle sort direction for a column
   * @param {string} sortBy - Column to sort by
   */
  toggleSortDirection(sortBy) {
    if (this.state.getSortBy() === sortBy) {
      this.state.toggleSortDirection();
    } else {
      this.state.setSortBy(sortBy);
      this.state.setSortDirection('asc');
    }
  }

  /**
   * Fetch events from the API
   */
  async fetchEvents() {
    this.ui.showLoading();
    try {
      const params = this.state.getQueryParams();
      const events = await this.api.getEvents(params);

      // If sorting by date, sort client-side
      const sortedEvents = this.state.getSortBy() === 'date'
        ? this.sortEventsByDate(events)
        : events;

      this.state.setEvents(sortedEvents);
      // Pass the tagManager to renderEvents
      this.ui.renderEvents(sortedEvents, this.state.getIncludeArchived(), this.tagManager);
      this.updateActionButtons();
      this.updateFilterTags();
    } catch (error) {
      console.error('Error fetching events:', error);
      this.ui.showNoEvents('Error loading events. Please try again.');
    } finally {
      this.ui.hideLoading();
    }
  }

  /**
   * Sort events by date
   * @param {Array} events - Events to sort
   * @returns {Array} - Sorted events
   */
  sortEventsByDate(events) {
    const sortDirection = this.state.getSortDirection() === 'asc' ? 1 : -1;

    return [...events].sort((a, b) => {
      const dateA = this.dateUtils.getEventFirstDate(a);
      const dateB = this.dateUtils.getEventFirstDate(b);

      if (!dateA && !dateB) return 0;
      if (!dateA) return 1;
      if (!dateB) return -1;

      return sortDirection * (new Date(dateA) - new Date(dateB));
    });
  }

  /**
   * Get IDs of selected events
   * @returns {Array<number>} - Selected event IDs
   */
  getSelectedEventIds() {
    const checkboxes = document.querySelectorAll('input[name="eventCheckbox"]:checked');
    return Array.from(checkboxes).map(checkbox => parseInt(checkbox.value));
  }

  /**
   * Update state of action buttons
   */
  updateActionButtons() {
    const selectedIds = this.getSelectedEventIds();
    const hasSelection = selectedIds.length > 0;

    this.ui.setActionButtonsState(hasSelection);
  }

  /**
   * Delete a single event
   * @param {number} eventId - ID of event to delete
   */
  async deleteEvent(eventId) {
    if (confirm('Are you sure you want to delete this event?')) {
      try {
        const result = await this.api.deleteEvent(eventId);
        if (result.success) {
          this.ui.removeEventFromUI(eventId);
          this.state.removeEvent(eventId);

          if (this.state.getEvents().length === 0) {
            this.ui.showNoEvents();
          }
        } else {
          alert('Error deleting event');
        }
      } catch (error) {
        console.error('Error deleting event:', error);
        alert('Error deleting event');
      }
    }
  }

  /**
   * Archive a single event
   * @param {number} eventId - ID of event to archive
   */
  async archiveEvent(eventId) {
    try {
      const result = await this.api.archiveEvent(eventId);
      if (result.success) {
        if (!this.state.getIncludeArchived()) {
          this.ui.removeEventFromUI(eventId);
          this.state.removeEvent(eventId);

          if (this.state.getEvents().length === 0) {
            this.ui.showNoEvents();
          }
        } else {
          // Refresh to update UI
          this.fetchEvents();
        }
      } else {
        alert('Error archiving event');
      }
    } catch (error) {
      console.error('Error archiving event:', error);
      alert('Error archiving event');
    }
  }

  /**
   * Delete multiple events
   * @param {Array<number>} eventIds - IDs of events to delete
   */
  async bulkDeleteEvents(eventIds) {
    this.ui.showLoading();
    try {
      const result = await this.api.bulkDeleteEvents(eventIds);
      if (result.success) {
        eventIds.forEach(id => {
          this.ui.removeEventFromUI(id);
          this.state.removeEvent(id);
        });

        if (this.state.getEvents().length === 0) {
          this.ui.showNoEvents();
        }

        this.ui.resetSelectAll();
        this.updateActionButtons();

        alert(`Successfully deleted ${result.deleted_count} events.`);
      } else {
        alert('Error deleting events');
      }
    } catch (error) {
      console.error('Error deleting events:', error);
      alert('Error deleting events');
    } finally {
      this.ui.hideLoading();
    }
  }

  /**
   * Archive multiple events
   * @param {Array<number>} eventIds - IDs of events to archive
   */
  async bulkArchiveEvents(eventIds) {
    this.ui.showArchiveLoading();
    try {
      const result = await this.api.bulkArchiveEvents(eventIds);
      if (result.success) {
        if (!this.state.getIncludeArchived()) {
          eventIds.forEach(id => {
            this.ui.removeEventFromUI(id);
            this.state.removeEvent(id);
          });

          if (this.state.getEvents().length === 0) {
            this.ui.showNoEvents();
          }
        } else {
          // Refresh to update UI
          this.fetchEvents();
        }

        this.ui.resetSelectAll();
        this.updateActionButtons();
        this.ui.hideArchiveModal();

        alert(`Successfully archived ${result.archived_count} events.`);
      } else {
        alert('Error archiving events');
      }
    } catch (error) {
      console.error('Error archiving events:', error);
      alert('Error archiving events');
    } finally {
      this.ui.hideArchiveLoading();
    }
  }

  /**
   * Export events to Google Calendar
   * @param {Array<number>} eventIds - IDs of events to export
   */
  async exportToCalendar(eventIds) {
    this.ui.showCalendarModal();
    try {
      const result = await this.api.exportToCalendar(eventIds);
      this.ui.displayCalendarResults(result);
    } catch (error) {
      console.error('Error exporting to calendar:', error);
      this.ui.displayCalendarError(error.message);
    }
  }

  /**
   * Handle tag filter changes
   * @param {string} tagName - Selected tag name
   */
  handleTagFilter(tagName) {
    this.state.setTagFilter(tagName);
    this.fetchEvents();
    this.updateFilterTags();
  }
}