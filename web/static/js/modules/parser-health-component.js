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
      this.ui.renderParserHealth(healthData, this.viewErrorDetails.bind(this));
    } catch (error) {
      console.error('Error fetching parser health:', error);
      // Display empty state or error message
      this.ui.renderParserHealth([], this.viewErrorDetails.bind(this));
    } finally {
      this.ui.hideLoading();
    }
  }

  /**
   * View detailed error message for a parser
   * @param {string} parserName - Name of the parser
   */
  async viewErrorDetails(parserName) {
    try {
      const details = await this.api.getParserErrorDetails(parserName);
      this.ui.showErrorDetails(details);
    } catch (error) {
      console.error('Error fetching error details:', error);
      // Show a fallback error message
      this.ui.showErrorDetails({
        display_name: parserName,
        error_message: 'Failed to load error details.',
        last_run: null
      });
    }
  }
}