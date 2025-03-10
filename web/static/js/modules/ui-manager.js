import { DateUtils } from './date-utils.js';

/**
 * Manages UI interactions and rendering
 */
export class UIManager {
  /**
   * @param {Function} eventHandler - Callback for UI events
   */
  constructor(eventHandler) {
    this.eventHandler = eventHandler;
    this.flatpickrInstance = null;
    this.dateUtils = new DateUtils();

    // Initialize UI elements
    this.elements = {
      eventsTableBody: document.getElementById('eventsTableBody'),
      loadingSpinner: document.getElementById('loadingSpinner'),
      noEventsMessage: document.getElementById('noEventsMessage'),
      filterInput: document.getElementById('filterInput'),
      filterButton: document.getElementById('filterButton'),
      dateRangeFilter: document.getElementById('dateRangeFilter'),
      clearDateButton: document.getElementById('clearDateButton'),
      showArchived: document.getElementById('showArchived'),
      selectAll: document.getElementById('selectAll'),
      bulkDeleteButton: document.getElementById('bulkDeleteButton'),
      bulkArchiveButton: document.getElementById('bulkArchiveButton'),
      exportCalendarButton: document.getElementById('exportCalendarButton'),
      confirmArchiveButton: document.getElementById('confirmArchiveButton'),
      archiveCount: document.getElementById('archiveCount'),
      archiveModalLoading: document.getElementById('archiveModalLoading'),
      calendarModalLoading: document.getElementById('calendarModalLoading'),
      calendarModalResults: document.getElementById('calendarModalResults'),
      calendarResultsList: document.getElementById('calendarResultsList'),
      filterTagsContainer: document.getElementById('filterTags')
    };

    // Initialize Bootstrap modals
    this.modals = {
      calendarModal: new bootstrap.Modal(document.getElementById('calendarModal')),
      bulkArchiveModal: new bootstrap.Modal(document.getElementById('bulkArchiveModal'))
    };

    // Initialize filter tags
    this.initFilterTags();
  }

  /**
   * Initialize the date range picker
   * @param {Function} changeHandler - Function to call when dates are selected
   */
  initializeDatePicker(changeHandler) {
    this.flatpickrInstance = flatpickr(this.elements.dateRangeFilter, {
      mode: "range",
      dateFormat: "Y-m-d",
      altInput: true,
      altFormat: "F j, Y",
      locale: {
        rangeSeparator: " to "
      },
      onChange: function(selectedDates) {
        if (selectedDates.length === 2) {
          changeHandler(selectedDates);
        }
      }
    });
  }

  /**
   * Initialize filter tags
   */
  initFilterTags() {
    // Listen for clicks on filter tags
    this.elements.filterTagsContainer.addEventListener('click', (e) => {
      if (e.target.matches('.filter-tag-close')) {
        const tagType = e.target.closest('.filter-tag').dataset.type;
        this.eventHandler('removeFilter', tagType);
      }
    });
  }

  /**
   * Update filter tags based on current filters
   * @param {Object} filters - Current filters
   */
  updateFilterTags(filters) {
    const container = this.elements.filterTagsContainer;
    container.innerHTML = '';

    // Tag filter tags
    if (filters.tag) {
      this.addFilterTag('tag', 'Tag', filters.tag);
    }

    // Text filter tag
    if (filters.text) {
      this.addFilterTag('text', 'Search', filters.text);
    }

    // Date range filter tag
    if (filters.dateStart && filters.dateEnd) {
      const formattedStart = this.dateUtils.formatDate(filters.dateStart.toISOString());
      const formattedEnd = this.dateUtils.formatDate(filters.dateEnd.toISOString());
      this.addFilterTag('date', 'Date Range', `${formattedStart} to ${formattedEnd}`);
    }

    // Archived filter tag
    if (filters.includeArchived) {
      this.addFilterTag('archived', 'Status', 'Including archived');
    }

    // Show or hide the container
    if (container.childElementCount > 0) {
      container.classList.remove('d-none');
    } else {
      container.classList.add('d-none');
    }
  }

  /**
   * Add a filter tag to the container
   * @param {string} type - Type of filter
   * @param {string} label - Tag label
   * @param {string} value - Tag value
   */
  addFilterTag(type, label, value) {
    const tag = document.createElement('div');
    tag.className = 'filter-tag';
    tag.dataset.type = type;

    tag.innerHTML = `
      <span class="filter-tag-label">${label}:</span>
      <span class="filter-tag-value">${this.escapeHTML(value)}</span>
      <i class="bi bi-x-circle filter-tag-close"></i>
    `;

    this.elements.filterTagsContainer.appendChild(tag);
  }

  /**
   * Clear the date picker
   */
  clearDatePicker() {
    if (this.flatpickrInstance) {
      this.flatpickrInstance.clear();
    }
  }

  /**
   * Show the loading spinner
   */
  showLoading() {
    this.elements.loadingSpinner.classList.remove('d-none');
    this.elements.noEventsMessage.classList.add('d-none');
  }

  /**
   * Hide the loading spinner
   */
  hideLoading() {
    this.elements.loadingSpinner.classList.add('d-none');
  }

  /**
   * Show the "no events" message
   * @param {string} message - Message to display (optional)
   */
  showNoEvents(message = 'No events found.') {
    this.elements.noEventsMessage.textContent = message;
    this.elements.noEventsMessage.classList.remove('d-none');
  }

  /**
   * Render the events list
   * @param events
   * @param includeArchived
   * @param tagManager
   */
  renderEvents(events, includeArchived, tagManager) {
    this.elements.eventsTableBody.innerHTML = '';

    if (events.length === 0) {
      this.showNoEvents();
      return;
    }

    events.forEach(event => {
      const row = document.createElement('tr');
      row.setAttribute('data-event-id', event.id);
      row.className = event.archived ? 'table-secondary' : '';

      // Format dates for display
      const dateStrings = event.dates.map(date => {
        let dateStr = this.dateUtils.formatDate(date.date);
        if (date.time) {
          dateStr += ` ${date.time}`;
        }
        if (date.end_date) {
          dateStr += ` - ${this.dateUtils.formatDate(date.end_date)}`;
          if (date.end_time) {
            dateStr += ` ${date.end_time}`;
          }
        }
        return dateStr;
      });

      const status = event.archived ? 'Archived' : 'Active';

      // Prepare the tags HTML using the TagManager
      const tagsHtml = tagManager ? tagManager.renderEventTags(event.tags) : '';

      row.innerHTML = `
      <td>
        <input type="checkbox" name="eventCheckbox" class="form-check-input" 
               value="${event.id}" onchange="updateActionButtons()">
      </td>
      <td>
        <div class="event-details">
          <div class="event-tags mb-1">${tagsHtml || '<span class="text-muted small">No tags</span>'}</div>
          <div class="event-title fw-semibold">${this.escapeHTML(event.title)}</div>
          <div class="event-description small text-muted">${this.escapeHTML(event.description)}</div>
          <div class="event-location small">${this.escapeHTML(event.location)}</div>
        </div>
      </td>
      <td>${dateStrings.join('<br>')}</td>
      <td>
        <span class="badge ${event.archived ? 'bg-secondary' : 'bg-success'}">${status}</span>
      </td>
      <td>
        <div class="btn-group">
          <a href="${event.url}" class="btn btn-sm btn-outline-primary" target="_blank">
            <i class="bi bi-box-arrow-up-right"></i>
          </a>
          ${!event.archived ?
        `<button class="btn btn-sm btn-outline-secondary archive-btn" data-event-id="${event.id}">
              <i class="bi bi-archive"></i>
            </button>` : ''}
          <button class="btn btn-sm btn-outline-danger delete-btn" data-event-id="${event.id}">
            <i class="bi bi-trash"></i>
          </button>
        </div>
      </td>
    `;

      this.elements.eventsTableBody.appendChild(row);
    });

    // Add event listeners for action buttons
    this.addEventListeners();

    this.elements.noEventsMessage.classList.add('d-none');
  }  renderEvents(events, includeArchived, tagManager) {
    this.elements.eventsTableBody.innerHTML = '';

    if (events.length === 0) {
      this.showNoEvents();
      return;
    }

    events.forEach(event => {
      const row = document.createElement('tr');
      row.setAttribute('data-event-id', event.id);
      row.className = event.archived ? 'table-secondary' : '';

      // Format dates for display
      const dateStrings = event.dates.map(date => {
        let dateStr = this.dateUtils.formatDate(date.date);
        if (date.time) {
          dateStr += ` ${date.time}`;
        }
        if (date.end_date) {
          dateStr += ` - ${this.dateUtils.formatDate(date.end_date)}`;
          if (date.end_time) {
            dateStr += ` ${date.end_time}`;
          }
        }
        return dateStr;
      });

      const status = event.archived ? 'Archived' : 'Active';

      // Prepare the tags HTML using the TagManager
      const tagsHtml = tagManager ? tagManager.renderEventTags(event.tags) : '';

      row.innerHTML = `
      <td>
        <input type="checkbox" name="eventCheckbox" class="form-check-input" 
               value="${event.id}" onchange="updateActionButtons()">
      </td>
      <td>
        <div class="event-details">
          <div class="event-title fw-semibold">${this.escapeHTML(event.title)}</div>
          <div class="event-description text-muted">${this.escapeHTML(event.description)}</div>
          <div class="event-location small">${this.escapeHTML(event.location)}</div>
          <div class="event-tags">${tagsHtml}</div>
        </div>
      </td>
      <td>${dateStrings.join('<br>')}</td>
      <td><span class="badge ${event.archived ? 'bg-secondary' : 'bg-success'}">${status}</span></td>
      <td>
        <div class="btn-group">
          <a href="${event.url}" class="btn btn-sm btn-outline-primary" target="_blank">
            <i class="bi bi-box-arrow-up-right"></i>
          </a>
          ${!event.archived ?
        `<button class="btn btn-sm btn-outline-secondary archive-btn" data-event-id="${event.id}">
              <i class="bi bi-archive"></i>
            </button>` : ''}
          <button class="btn btn-sm btn-outline-danger delete-btn" data-event-id="${event.id}">
            <i class="bi bi-trash"></i>
          </button>
        </div>
      </td>
    `;

      this.elements.eventsTableBody.appendChild(row);
    });

    // Add event listeners for action buttons
    this.addEventListeners();

    this.elements.noEventsMessage.classList.add('d-none');
  }

  /**
   * Add event listeners to dynamically created elements
   */
  addEventListeners() {
    // Delete buttons
    document.querySelectorAll('.delete-btn').forEach(button => {
      button.addEventListener('click', () => {
        const eventId = parseInt(button.getAttribute('data-event-id'));
        this.eventHandler('delete', eventId);
      });
    });

    // Archive buttons
    document.querySelectorAll('.archive-btn').forEach(button => {
      button.addEventListener('click', () => {
        const eventId = parseInt(button.getAttribute('data-event-id'));
        this.eventHandler('archive', eventId);
      });
    });
  }

  /**
   * Select or deselect all events
   * @param {boolean} checked - Whether to check or uncheck all
   */
  selectAllEvents(checked) {
    const checkboxes = document.querySelectorAll('input[name="eventCheckbox"]');
    checkboxes.forEach(checkbox => {
      checkbox.checked = checked;
    });
  }

  /**
   * Reset the "select all" checkbox
   */
  resetSelectAll() {
    this.elements.selectAll.checked = false;
  }

  /**
   * Remove an event from the UI
   * @param {number} eventId - ID of the event to remove
   */
  removeEventFromUI(eventId) {
    const row = document.querySelector(`tr[data-event-id="${eventId}"]`);
    if (row) {
      row.remove();
    }
  }

  /**
   * Enable or disable action buttons based on selection
   * @param {boolean} hasSelection - Whether any events are selected
   */
  setActionButtonsState(hasSelection) {
    this.elements.bulkDeleteButton.disabled = !hasSelection;
    this.elements.bulkArchiveButton.disabled = !hasSelection;
    this.elements.exportCalendarButton.disabled = !hasSelection;
  }

  /**
   * Show the archive confirmation modal
   * @param {number} count - Number of events to archive
   */
  showArchiveConfirmation(count) {
    this.elements.archiveCount.textContent = count;
    this.modals.bulkArchiveModal.show();
  }

  /**
   * Show loading state in the archive modal
   */
  showArchiveLoading() {
    this.elements.archiveModalLoading.classList.remove('d-none');
    this.elements.confirmArchiveButton.disabled = true;
  }

  /**
   * Hide loading state in the archive modal
   */
  hideArchiveLoading() {
    this.elements.archiveModalLoading.classList.add('d-none');
    this.elements.confirmArchiveButton.disabled = false;
  }

  /**
   * Hide the archive modal
   */
  hideArchiveModal() {
    this.modals.bulkArchiveModal.hide();
  }

  /**
   * Show the calendar export modal
   */
  showCalendarModal() {
    this.elements.calendarModalResults.classList.add('d-none');
    this.elements.calendarModalLoading.classList.remove('d-none');
    this.elements.calendarResultsList.innerHTML = '';
    this.modals.calendarModal.show();
  }

  /**
   * Display calendar export results
   * @param {Object} data - Results data
   */
  displayCalendarResults(data) {
    this.elements.calendarModalLoading.classList.add('d-none');
    this.elements.calendarModalResults.classList.remove('d-none');

    if (data.results) {
      data.results.forEach(result => {
        const listItem = document.createElement('li');
        listItem.className = `list-group-item ${result.success ? 'list-group-item-success' : 'list-group-item-danger'}`;

        listItem.innerHTML = `
          <strong>${this.escapeHTML(result.title)}</strong>: 
          ${result.success ? 'Successfully exported' : `Failed: ${this.escapeHTML(result.error)}`}
        `;

        this.elements.calendarResultsList.appendChild(listItem);
      });
    } else if (data.error) {
      this.displayCalendarError(data.error);
    }
  }

  /**
   * Display an error in the calendar modal
   * @param {string} error - Error message
   */
  displayCalendarError(error) {
    this.elements.calendarModalLoading.classList.add('d-none');
    this.elements.calendarModalResults.classList.remove('d-none');

    const errorItem = document.createElement('li');
    errorItem.className = 'list-group-item list-group-item-danger';
    errorItem.textContent = `Error: ${error}`;
    this.elements.calendarResultsList.appendChild(errorItem);
  }

  /**
   * Truncate text to specified length
   * @param {string} text - Text to truncate
   * @param {number} maxLength - Maximum length
   * @returns {string} - Truncated text
   */
  truncateText(text, maxLength) {
    if (!text) return '';
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
  }

  /**
   * Escape HTML special characters
   * @param {string} str - String to escape
   * @returns {string} - Escaped string
   */
  escapeHTML(str) {
    if (!str) return '';
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }
}