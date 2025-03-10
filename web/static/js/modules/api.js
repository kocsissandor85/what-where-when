/**
 * API interface for event-related operations
 */
export class EventAPI {
  /**
   * Fetch events with optional filtering
   * @param {Object} params - Query parameters
   * @returns {Promise<Array>} - Array of event objects
   */
  async getEvents(params) {
    const queryString = new URLSearchParams(params).toString();
    const response = await fetch(`/api/events?${queryString}`);

    if (!response.ok) {
      throw new Error('Network response was not ok');
    }

    return await response.json();
  }

  /**
   * Delete a single event
   * @param {number} eventId - ID of the event to delete
   * @returns {Promise<Object>} - Result object
   */
  async deleteEvent(eventId) {
    const response = await fetch(`/api/events/${eventId}`, {
      method: 'DELETE'
    });

    if (!response.ok) {
      throw new Error('Network response was not ok');
    }

    return await response.json();
  }

  /**
   * Archive a single event
   * @param {number} eventId - ID of the event to archive
   * @returns {Promise<Object>} - Result object
   */
  async archiveEvent(eventId) {
    const response = await fetch(`/api/events/${eventId}/archive`, {
      method: 'PUT'
    });

    if (!response.ok) {
      throw new Error('Network response was not ok');
    }

    return await response.json();
  }

  /**
   * Delete multiple events
   * @param {Array<number>} eventIds - Array of event IDs to delete
   * @returns {Promise<Object>} - Result object
   */
  async bulkDeleteEvents(eventIds) {
    const response = await fetch('/api/events/bulk-delete', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ event_ids: eventIds })
    });

    if (!response.ok) {
      throw new Error('Network response was not ok');
    }

    return await response.json();
  }

  /**
   * Archive multiple events
   * @param {Array<number>} eventIds - Array of event IDs to archive
   * @returns {Promise<Object>} - Result object
   */
  async bulkArchiveEvents(eventIds) {
    const response = await fetch('/api/events/bulk-archive', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ event_ids: eventIds })
    });

    if (!response.ok) {
      throw new Error('Network response was not ok');
    }

    return await response.json();
  }

  /**
   * Export events to Google Calendar
   * @param {Array<number>} eventIds - Array of event IDs to export
   * @returns {Promise<Object>} - Result object
   */
  async exportToCalendar(eventIds) {
    const response = await fetch('/api/events/export-calendar', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ event_ids: eventIds })
    });

    if (!response.ok) {
      throw new Error('Network response was not ok');
    }

    return await response.json();
  }
}