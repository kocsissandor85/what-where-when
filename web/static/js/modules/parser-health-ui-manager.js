/**
 * Manages the parser health UI
 */
export class ParserHealthUIManager {
  /**
   * @param {Function} refreshCallback - Callback for when health data is refreshed
   */
  constructor(refreshCallback = null) {
    this.refreshCallback = refreshCallback;
    this.errorModal = null;

    // Initialize UI elements
    this.elements = {
      parserHealthTable: document.getElementById('parserHealthTable'),
      parserHealthTableBody: document.getElementById('parserHealthTableBody'),
      parserHealthCard: document.getElementById('parserHealthCard'),
      parserHealthCardBody: document.getElementById('parserHealthCardBody'),
      loadingSpinner: document.getElementById('parserHealthLoading'),
      toggleHealthButton: document.querySelector('#parserHealthCard .toggle-btn'),
      refreshHealthButton: document.getElementById('refreshHealthButton'),
      errorModal: document.getElementById('errorDetailsModal'),
      errorModalTitle: document.getElementById('errorModalTitle'),
      errorModalContent: document.getElementById('errorModalContent'),
      errorModalDate: document.getElementById('errorModalDate')
    };

    // Initialize Bootstrap modal
    if (this.elements.errorModal) {
      this.errorModal = new bootstrap.Modal(this.elements.errorModal);
    }

    // Add event listeners
    if (this.elements.refreshHealthButton) {
      this.elements.refreshHealthButton.addEventListener('click', () => {
        if (this.refreshCallback) {
          this.refreshCallback();
        }
      });
    }
  }

  /**
   * Toggle the visibility of the parser health card
   */
  toggleHealthCard() {
    if (this.elements.parserHealthCardBody) {
      if (this.elements.parserHealthCardBody.classList.contains('d-none')) {
        this.elements.parserHealthCardBody.classList.remove('d-none');
        this.elements.toggleHealthButton.innerHTML = '<i class="bi bi-chevron-up"></i>';
        this.elements.parserHealthCard.classList.remove('collapsed');
      } else {
        this.elements.parserHealthCardBody.classList.add('d-none');
        this.elements.toggleHealthButton.innerHTML = '<i class="bi bi-chevron-down"></i>';
        this.elements.parserHealthCard.classList.add('collapsed');
      }
    }
  }

  /**
   * Show loading spinner
   */
  showLoading() {
    if (this.elements.loadingSpinner) {
      this.elements.loadingSpinner.classList.remove('d-none');
    }
  }

  /**
   * Hide loading spinner
   */
  hideLoading() {
    if (this.elements.loadingSpinner) {
      this.elements.loadingSpinner.classList.add('d-none');
    }
  }

  /**
   * Show the error details modal
   * @param {Object} data - Error details data
   */
  showErrorDetails(data) {
    if (!this.errorModal) return;

    // Set modal content
    this.elements.errorModalTitle.textContent = `Error Details - ${data.display_name}`;
    this.elements.errorModalContent.textContent = data.error_message;

    // Format date
    if (data.last_run) {
      const date = new Date(data.last_run);
      this.elements.errorModalDate.textContent = `${date.toLocaleDateString()} ${date.toLocaleTimeString()}`;
    } else {
      this.elements.errorModalDate.textContent = 'Unknown';
    }

    // Show modal
    this.errorModal.show();
  }

  /**
   * Render parser health data
   * @param {Array} healthData - Array of parser health records
   * @param {Function} errorDetailsCallback - Callback for viewing error details
   */
  renderParserHealth(healthData, errorDetailsCallback) {
    if (!this.elements.parserHealthTableBody) return;

    this.elements.parserHealthTableBody.innerHTML = '';

    if (healthData.length === 0) {
      const row = document.createElement('tr');
      row.innerHTML = '<td colspan="5" class="text-center">No parser health data available.</td>';
      this.elements.parserHealthTableBody.appendChild(row);
      return;
    }

    healthData.forEach(record => {
      const row = document.createElement('tr');

      // Format date
      const lastRun = record.last_run ? new Date(record.last_run) : null;
      const formattedDate = lastRun ?
        lastRun.toLocaleDateString() + ' ' + lastRun.toLocaleTimeString() :
        'Never';

      // Create status badge
      const statusBadge = record.success ?
        '<span class="badge bg-success">Success</span>' :
        '<span class="badge bg-danger">Failed</span>';

      // Create error cell content - now a button for failed parsers
      let errorCell;
      if (!record.success && record.error_message) {
        errorCell = `<button class="btn btn-sm btn-outline-danger view-error-btn" 
                            data-parser="${this.escapeHTML(record.parser_name)}">
                      <i class="bi bi-exclamation-circle me-1"></i>View Error
                    </button>`;
      } else {
        errorCell = '-';
      }

      row.innerHTML = `
        <td>${this.escapeHTML(record.display_name)}</td>
        <td>${formattedDate}</td>
        <td class="text-center">${statusBadge}</td>
        <td class="text-center">${record.events_parsed}</td>
        <td>${errorCell}</td>
      `;

      this.elements.parserHealthTableBody.appendChild(row);
    });

    // Add event listeners to error buttons
    document.querySelectorAll('.view-error-btn').forEach(button => {
      button.addEventListener('click', () => {
        const parserName = button.getAttribute('data-parser');
        if (errorDetailsCallback) {
          errorDetailsCallback(parserName);
        }
      });
    });
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