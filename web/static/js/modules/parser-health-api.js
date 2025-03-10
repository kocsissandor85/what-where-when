/**
 * API interface for parser health operations
 */
export class ParserHealthAPI {
  /**
   * Fetch parser health data
   * @returns {Promise<Array>} - Array of parser health records
   */
  async getParserHealth() {
    const response = await fetch('/api/parser-health');

    if (!response.ok) {
      throw new Error('Network response was not ok');
    }

    const data = await response.json();
    return data.parser_health || [];
  }

  /**
   * Fetch detailed error information for a parser
   * @param {string} parserName - Name of the parser
   * @returns {Promise<Object>} - Error details
   */
  async getParserErrorDetails(parserName) {
    const response = await fetch(`/api/parser-health/error-details/${parserName}`);

    if (!response.ok) {
      throw new Error('Network response was not ok');
    }

    return await response.json();
  }
}