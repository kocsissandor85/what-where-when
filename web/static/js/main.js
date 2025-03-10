document.addEventListener('DOMContentLoaded', function() {
  // DOM elements
  const eventsTableBody = document.getElementById('eventsTableBody');
  const loadingSpinner = document.getElementById('loadingSpinner');
  const noEventsMessage = document.getElementById('noEventsMessage');
  const filterInput = document.getElementById('filterInput');
  const filterButton = document.getElementById('filterButton');
  const showArchived = document.getElementById('showArchived');
  const selectAll = document.getElementById('selectAll');
  const bulkDeleteButton = document.getElementById('bulkDeleteButton');
  const exportCalendarButton = document.getElementById('exportCalendarButton');
  const calendarModal = new bootstrap.Modal(document.getElementById('calendarModal'));
  const calendarModalLoading = document.getElementById('calendarModalLoading');
  const calendarModalResults = document.getElementById('calendarModalResults');
  const calendarResultsList = document.getElementById('calendarResultsList');

  // State variables
  let events = [];
  let currentFilter = '';
  let currentSortBy = 'title';
  let currentSortDir = 'asc';
  let includeArchived = false;

  // Initialize the events table
  fetchEvents();

  // Event listeners
  filterButton.addEventListener('click', applyFilter);
  filterInput.addEventListener('keyup', function(event) {
    if (event.key === 'Enter') {
      applyFilter();
    }
  });

  showArchived.addEventListener('change', function() {
    includeArchived = this.checked;
    fetchEvents();
  });

  selectAll.addEventListener('change', function() {
    const checkboxes = document.querySelectorAll('input[name="eventCheckbox"]');
    checkboxes.forEach(checkbox => {
      checkbox.checked = this.checked;
    });
    updateActionButtons();
  });

  bulkDeleteButton.addEventListener('click', function() {
    const selectedIds = getSelectedEventIds();
    if (selectedIds.length > 0 && confirm(`Are you sure you want to delete ${selectedIds.length} events?`)) {
      bulkDeleteEvents(selectedIds);
    }
  });

  exportCalendarButton.addEventListener('click', function() {
    const selectedIds = getSelectedEventIds();
    if (selectedIds.length > 0) {
      exportToCalendar(selectedIds);
    }
  });

  // Add click events for sortable columns
  document.querySelectorAll('th[data-sort]').forEach(th => {
    th.addEventListener('click', function() {
      const sortBy = this.getAttribute('data-sort');
      if (currentSortBy === sortBy) {
        currentSortDir = currentSortDir === 'asc' ? 'desc' : 'asc';
      } else {
        currentSortBy = sortBy;
        currentSortDir = 'asc';
      }
      fetchEvents();
    });
  });

  // Functions
  function fetchEvents() {
    showLoading();

    // Construct the query parameters
    const params = new URLSearchParams({
      filter: currentFilter,
      sort_by: currentSortBy,
      sort_dir: currentSortDir,
      include_archived: includeArchived
    });

    fetch(`/api/events?${params}`)
      .then(response => {
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        return response.json();
      })
      .then(data => {
        events = data;
        renderEvents();
        hideLoading();
      })
      .catch(error => {
        console.error('Error fetching events:', error);
        showNoEvents('Error loading events. Please try again.');
        hideLoading();
      });
  }

  function renderEvents() {
    eventsTableBody.innerHTML = '';

    if (events.length === 0) {
      showNoEvents();
      return;
    }

    events.forEach(event => {
      const row = document.createElement('tr');
      row.setAttribute('data-event-id', event.id);
      row.className = event.archived ? 'table-secondary' : '';

      // Format dates for display
      const dateStrings = event.dates.map(date => {
        let dateStr = formatDate(date.date);
        if (date.time) {
          dateStr += ` ${date.time}`;
        }
        if (date.end_date) {
          dateStr += ` - ${formatDate(date.end_date)}`;
          if (date.end_time) {
            dateStr += ` ${date.end_time}`;
          }
        }
        return dateStr;
      });

      const status = event.archived ? 'Archived' : 'Active';

      row.innerHTML = `
                <td>
                    <input type="checkbox" name="eventCheckbox" class="form-check-input" 
                           value="${event.id}" onchange="updateActionButtons()">
                </td>
                <td>${escapeHTML(event.title)}</td>
                <td>${escapeHTML(truncateText(event.description, 100))}</td>
                <td>${escapeHTML(event.location)}</td>
                <td>${dateStrings.join('<br>')}</td>
                <td><span class="badge ${event.archived ? 'bg-secondary' : 'bg-success'}">${status}</span></td>
                <td>
                    <div class="btn-group">
                        <a href="${event.url}" class="btn btn-sm btn-outline-primary" target="_blank">
                            <i class="bi bi-box-arrow-up-right"></i>
                        </a>
                        <button class="btn btn-sm btn-outline-danger delete-btn" data-event-id="${event.id}">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </td>
            `;

      eventsTableBody.appendChild(row);
    });

    // Add event listeners for delete buttons
    document.querySelectorAll('.delete-btn').forEach(button => {
      button.addEventListener('click', function() {
        const eventId = this.getAttribute('data-event-id');
        deleteEvent(eventId);
      });
    });

    noEventsMessage.classList.add('d-none');
    updateActionButtons();
  }

  function applyFilter() {
    currentFilter = filterInput.value.trim();
    fetchEvents();
  }

  function deleteEvent(eventId) {
    if (confirm('Are you sure you want to delete this event?')) {
      fetch(`/api/events/${eventId}`, { method: 'DELETE' })
        .then(response => {
          if (!response.ok) {
            throw new Error('Network response was not ok');
          }
          return response.json();
        })
        .then(data => {
          if (data.success) {
            // Remove from UI
            const row = document.querySelector(`tr[data-event-id="${eventId}"]`);
            if (row) {
              row.remove();
            }

            // Remove from our local array
            events = events.filter(event => event.id != eventId);

            if (events.length === 0) {
              showNoEvents();
            }
          } else {
            alert('Error deleting event');
          }
        })
        .catch(error => {
          console.error('Error deleting event:', error);
          alert('Error deleting event');
        });
    }
  }

  function bulkDeleteEvents(eventIds) {
    showLoading();

    fetch('/api/events/bulk-delete', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ event_ids: eventIds })
    })
      .then(response => {
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        return response.json();
      })
      .then(data => {
        if (data.success) {
          // Remove deleted events from UI
          eventIds.forEach(id => {
            const row = document.querySelector(`tr[data-event-id="${id}"]`);
            if (row) {
              row.remove();
            }
          });

          // Remove from our local array
          events = events.filter(event => !eventIds.includes(event.id));

          if (events.length === 0) {
            showNoEvents();
          }

          // Reset select all checkbox
          selectAll.checked = false;
          updateActionButtons();

          alert(`Successfully deleted ${data.deleted_count} events.`);
        } else {
          alert('Error deleting events');
        }
        hideLoading();
      })
      .catch(error => {
        console.error('Error deleting events:', error);
        alert('Error deleting events');
        hideLoading();
      });
  }

  function exportToCalendar(eventIds) {
    // Reset modal content
    calendarModalResults.classList.add('d-none');
    calendarModalLoading.classList.remove('d-none');
    calendarResultsList.innerHTML = '';

    // Show modal
    calendarModal.show();

    // Make API call
    fetch('/api/events/export-calendar', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ event_ids: eventIds })
    })
      .then(response => {
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        return response.json();
      })
      .then(data => {
        if (data.results) {
          // Show results
          calendarModalLoading.classList.add('d-none');
          calendarModalResults.classList.remove('d-none');

          // Add results to list
          data.results.forEach(result => {
            const listItem = document.createElement('li');
            listItem.className = `list-group-item ${result.success ? 'list-group-item-success' : 'list-group-item-danger'}`;

            listItem.innerHTML = `
                            <strong>${escapeHTML(result.title)}</strong>: 
                            ${result.success ? 'Successfully exported' : `Failed: ${escapeHTML(result.error)}`}
                        `;

            calendarResultsList.appendChild(listItem);
          });
        } else if (data.error) {
          // Show error
          calendarModalLoading.classList.add('d-none');
          calendarModalResults.classList.remove('d-none');

          const errorItem = document.createElement('li');
          errorItem.className = 'list-group-item list-group-item-danger';
          errorItem.textContent = `Error: ${data.error}`;
          calendarResultsList.appendChild(errorItem);
        }
      })
      .catch(error => {
        console.error('Error exporting to calendar:', error);

        // Show error in modal
        calendarModalLoading.classList.add('d-none');
        calendarModalResults.classList.remove('d-none');

        const errorItem = document.createElement('li');
        errorItem.className = 'list-group-item list-group-item-danger';
        errorItem.textContent = `Error: ${error.message}`;
        calendarResultsList.appendChild(errorItem);
      });
  }

  function getSelectedEventIds() {
    const checkboxes = document.querySelectorAll('input[name="eventCheckbox"]:checked');
    return Array.from(checkboxes).map(checkbox => parseInt(checkbox.value));
  }

  function updateActionButtons() {
    const selectedIds = getSelectedEventIds();
    bulkDeleteButton.disabled = selectedIds.length === 0;
    exportCalendarButton.disabled = selectedIds.length === 0;
  }

  // This needs to be in global scope for the inline handler
  window.updateActionButtons = updateActionButtons;

  function showLoading() {
    loadingSpinner.classList.remove('d-none');
    noEventsMessage.classList.add('d-none');
  }

  function hideLoading() {
    loadingSpinner.classList.add('d-none');
  }

  function showNoEvents(message = 'No events found.') {
    noEventsMessage.textContent = message;
    noEventsMessage.classList.remove('d-none');
  }

  // Helper functions
  function formatDate(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString();
  }

  function truncateText(text, maxLength) {
    if (!text) return '';
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
  }

  function escapeHTML(str) {
    if (!str) return '';
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }
});