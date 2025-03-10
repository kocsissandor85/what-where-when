/**
 * API interface for tag-related operations
 */
export class TagAPI {
  /**
   * Fetch all available tags
   * @returns {Promise<Array>} - Array of tag objects
   */
  async getTags() {
    const response = await fetch('/api/tags');

    if (!response.ok) {
      throw new Error('Network response was not ok');
    }

    return await response.json();
  }
}