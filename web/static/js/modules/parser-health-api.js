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
}