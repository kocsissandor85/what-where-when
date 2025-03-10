import { TagMappingAPI } from './tag-mapping-api.js';

/**
 * Manages the UI for tag mappings
 */
export class TagMappingUIManager {
  constructor() {
    this.api = new TagMappingAPI();

    // Initialize UI elements
    this.elements = {
      modal: document.getElementById('tagMappingModal'),
      mappingsTableBody: document.getElementById('tagMappingTableBody'),
      sourceTagInput: document.getElementById('sourceTaxInput'),
      displayTagInput: document.getElementById('displayTagInput'),
      addMappingButton: document.getElementById('addTagMappingBtn'),
      addMappingErrorAlert: document.getElementById('addTagMappingErrorAlert')
    };

    // Initialize Bootstrap modal
    this.modal = new bootstrap.Modal(this.elements.modal);

    // Bind event listeners
    this.setupEventListeners();
  }

  /**
   * Set up event listeners for tag mapping interactions
   */
  setupEventListeners() {
    // Add mapping button
    if (this.elements.addMappingButton) {
      this.elements.addMappingButton.addEventListener('click', () => this.addTagMapping());
    }

    // Delegation for delete buttons
    if (this.elements.mappingsTableBody) {
      this.elements.mappingsTableBody.addEventListener('click', (event) => {
        const deleteBtn = event.target.closest('.delete-mapping-btn');
        if (deleteBtn) {
          const sourceTag = deleteBtn.getAttribute('data-source-tag');
          this.deleteTagMapping(sourceTag);
        }
      });
    }
  }

  /**
   * Fetch and render tag mappings
   */
  async loadTagMappings() {
    try {
      const mappings = await this.api.getTagMappings();
      this.renderTagMappings(mappings);
    } catch (error) {
      console.error('Error loading tag mappings:', error);
      this.showErrorAlert('Failed to load tag mappings');
    }
  }

  /**
   * Render tag mappings in the table
   * @param {Array} mappings - Tag mapping objects
   */
  renderTagMappings(mappings) {
    if (!this.elements.mappingsTableBody) return;

    // Clear existing rows
    this.elements.mappingsTableBody.innerHTML = '';

    if (mappings.length === 0) {
      const noDataRow = document.createElement('tr');
      noDataRow.innerHTML = '<td colspan="3" class="text-center text-muted">No tag mappings found</td>';
      this.elements.mappingsTableBody.appendChild(noDataRow);
      return;
    }

    mappings.forEach(mapping => {
      const row = document.createElement('tr');
      row.innerHTML = `
        <td>${this.escapeHTML(mapping.source_tag)}</td>
        <td>${this.escapeHTML(mapping.display_tag)}</td>
        <td class="text-end">
          <button class="btn btn-sm btn-outline-danger delete-mapping-btn" 
                  data-source-tag="${this.escapeHTML(mapping.source_tag)}">
            <i class="bi bi-trash"></i>
          </button>
        </td>
      `;
      this.elements.mappingsTableBody.appendChild(row);
    });
  }

  /**
   * Add a new tag mapping
   */
  async addTagMapping() {
    // Reset error state
    this.hideErrorAlert();

    // Get input values
    const sourceTag = this.elements.sourceTagInput.value.trim();
    const displayTag = this.elements.displayTagInput.value.trim();

    // Validate inputs
    if (!sourceTag || !displayTag) {
      this.showErrorAlert('Please enter both source and display tags');
      return;
    }

    try {
      // Create mapping
      await this.api.createTagMapping(sourceTag, displayTag);

      // Refresh mappings
      await this.loadTagMappings();

      // Clear inputs
      this.elements.sourceTagInput.value = '';
      this.elements.displayTagInput.value = '';
    } catch (error) {
      console.error('Error adding tag mapping:', error);
      this.showErrorAlert(error.message || 'Failed to add tag mapping');
    }
  }

  /**
   * Delete a tag mapping
   * @param {string} sourceTag - Source tag to delete mapping for
   */
  async deleteTagMapping(sourceTag) {
    try {
      await this.api.deleteTagMapping(sourceTag);
      await this.loadTagMappings();
    } catch (error) {
      console.error('Error deleting tag mapping:', error);
      this.showErrorAlert(error.message || 'Failed to delete tag mapping');
    }
  }

  /**
   * Show error alert
   * @param {string} message - Error message to display
   */
  showErrorAlert(message) {
    if (this.elements.addMappingErrorAlert) {
      this.elements.addMappingErrorAlert.textContent = message;
      this.elements.addMappingErrorAlert.classList.remove('d-none');
    }
  }

  /**
   * Hide error alert
   */
  hideErrorAlert() {
    if (this.elements.addMappingErrorAlert) {
      this.elements.addMappingErrorAlert.classList.add('d-none');
    }
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