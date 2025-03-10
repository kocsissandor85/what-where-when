/**
 * Manages the parser health UI
 */
export class ParserHealthUIManager {
  /**
   * @param {Function} refreshCallback - Callback for when health data is refreshed
   */
  constructor(refreshCallback = null) {
    this.refreshCallback = refreshCallback;

    // Initialize UI elements
    this.elements = {
      parserHealthTable: document.getElementById('parserHealthTable'),
      parserHealthBody: document.getElementById('parserHealthBody'),
      parserHealthCard: document.getElementById('parserHealthCard'),
      loadingSpinner: document.getElementById('parserHealthLoading'),
      toggleHealthButton: document.getElementById('toggleHealthButton'),
      refreshHealthButton: document.getElementById('refreshHealthButton')
    };

    // Add event listeners
    if (this.elements.toggleHealthButton) {
      this.elements.toggleHealthButton.addEventListener('click', () => {
        this.toggleHealthCard();
      });
    }

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
    if (this.elements.parserHealthCard) {
      const cardBody = this.elements.parserHealthCard.querySelector('.card-body');

      if (cardBody.classList.contains('d-none')) {
        cardBody.classList.remove('d-none');
        this.elements.toggleHealthButton.innerHTML = '<i class="bi bi-chevron-up"></i>';
      } else {
        cardBody.classList.add('d-none');
        this.elements.toggleHealthButton.innerHTML = '<i class="bi bi-chevron-down"></i>';
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
   * Render parser health data
   * @param {Array} healthData - Array of parser health records
   */
  renderParserHealth(healthData) {
    if (!this.elements.parserHealthBody) return;

    this.elements.parserHealthBody.innerHTML = '';

    if (healthData.length === 0) {
      const row = document.createElement('tr');
      row.innerHTML = '<td colspan="5" class="text-center">No parser health data available.</td>';
      this.elements.parserHealthBody.appendChild(row);
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

      row.innerHTML = `
        <td>${this.escapeHTML(record.parser_name)}</td>
        <td>${formattedDate}</td>
        <td class="text-center">${statusBadge}</td>
        <td class="text-center">${record.events_parsed}</td>
        <td>${this.escapeHTML(record.error_message || '-')}</td>
      `;

      this.elements.parserHealthBody.appendChild(row);
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