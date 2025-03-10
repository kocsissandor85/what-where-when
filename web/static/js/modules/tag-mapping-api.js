/**
 * API interface for tag mapping operations
 */
export class TagMappingAPI {
  /**
   * Fetch all tag mappings
   * @returns {Promise<Array>} - Array of tag mapping objects
   */
  async getTagMappings() {
    const response = await fetch('/api/tags/mappings');

    if (!response.ok) {
      throw new Error('Network response was not ok');
    }

    return await response.json();
  }

  /**
   * Create or update a tag mapping
   * @param {string} sourceTag - Source tag name
   * @param {string} displayTag - Display tag name
   * @returns {Promise<Object>} - Created or updated mapping
   */
  async createTagMapping(sourceTag, displayTag) {
    const response = await fetch('/api/tags/mappings', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ source_tag: sourceTag, display_tag: displayTag })
    });

    if (!response.ok) {
      throw new Error('Network response was not ok');
    }

    return await response.json();
  }

  /**
   * Delete a tag mapping
   * @param {string} sourceTag - Source tag to remove mapping for
   * @returns {Promise<Object>} - Deletion result
   */
  async deleteTagMapping(sourceTag) {
    const response = await fetch(`/api/tags/mappings/${encodeURIComponent(sourceTag)}`, {
      method: 'DELETE'
    });

    if (!response.ok) {
      throw new Error('Network response was not ok');
    }

    return await response.json();
  }
}