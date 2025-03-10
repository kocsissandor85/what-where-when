// Main entry point for the application
import { EventManagerApp } from './modules/app.js';

// Create a single instance of the app when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
  // Initialize the application and store the instance globally
  window.eventManagerApp = new EventManagerApp();
  window.eventManagerApp.init();
});

// Make updateActionButtons available globally for inline handlers
window.updateActionButtons = function() {
  if (window.eventManagerApp) {
    window.eventManagerApp.updateActionButtons();
  }
};