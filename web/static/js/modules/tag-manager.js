import { TagAPI } from './tag-api.js';

/**
 * Manages tag UI components and operations
 */
export class TagManager {
  /**
   * @param {Function} filterCallback - Callback for when a tag is selected
   */
  constructor(filterCallback) {
    this.api = new TagAPI();
    this.filterCallback = filterCallback;
    this.tags = [];

    // Initialize UI elements
    this.elements = {
      tagFilterContainer: document.getElementById('tagFilterContainer'),
      tagDropdown: document.getElementById('tagDropdown'),
      selectedTagsContainer: document.getElementById('selectedTags')
    };

    this.init();
  }

  /**
   * Initialize the tag manager
   */
  async init() {
    try {
      await this.loadTags();
      this.setupEventListeners();
    } catch (error) {
      console.error('Error initializing tag manager:', error);
    }
  }

  /**
   * Load all available tags from the API
   */
  async loadTags() {
    try {
      this.tags = await this.api.getTags();
      this.renderTagDropdown();
    } catch (error) {
      console.error('Error loading tags:', error);
    }
  }

  /**
   * Render the tag dropdown
   */
  renderTagDropdown() {
    if (!this.elements.tagDropdown) return;

    // Clear existing options
    this.elements.tagDropdown.innerHTML = '<option value="">Select a tag</option>';

    // Add tag options
    this.tags.forEach(tag => {
      const option = document.createElement('option');
      option.value = tag.name;
      option.textContent = tag.name;
      this.elements.tagDropdown.appendChild(option);
    });
  }

  /**
   * Set up event listeners
   */
  setupEventListeners() {
    if (this.elements.tagDropdown) {
      this.elements.tagDropdown.addEventListener('change', () => {
        const selectedTag = this.elements.tagDropdown.value;
        if (selectedTag) {
          this.selectTag(selectedTag);
          this.elements.tagDropdown.value = ''; // Reset dropdown
        }
      });
    }
  }

  /**
   * Handle tag selection
   * @param {string} tagName - Name of the selected tag
   */
  selectTag(tagName) {
    if (this.filterCallback) {
      this.filterCallback(tagName);
    }
  }

  /**
   * Render an event's tags in the event row
   * @param {Array} tags - Array of tag objects
   * @returns {string} - HTML for tags
   */
  renderEventTags(tags) {
    if (!tags || tags.length === 0) {
      return '<span class="text-muted">No tags</span>';
    }

    return tags.map(tag => `
      <span class="badge bg-secondary me-1">${this.escapeHTML(tag.name)}</span>
    `).join('');
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