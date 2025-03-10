import { ParserHealthAPI } from './parser-health-api.js';
import { ParserHealthUIManager } from './parser-health-ui-manager.js';

/**
 * Parser Health Component
 */
export class ParserHealthComponent {
  constructor() {
    this.api = new ParserHealthAPI();
    this.ui = new ParserHealthUIManager(this.fetchParserHealth.bind(this));
  }

  /**
   * Initialize the component
   */
  init() {
    this.fetchParserHealth();
  }

  /**
   * Fetch parser health data from the API
   */
  async fetchParserHealth() {
    this.ui.showLoading();

    try {
      const healthData = await this.api.getParserHealth();
      this.ui.renderParserHealth(healthData);
    } catch (error) {
      console.error('Error fetching parser health:', error);
      // Display empty state or error message
      this.ui.renderParserHealth([]);
    } finally {
      this.ui.hideLoading();
    }
  }
}