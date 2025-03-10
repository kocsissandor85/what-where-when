// Main entry point for the application
import { EventManagerApp } from './modules/app.js';
import { ParserHealthComponent } from './modules/parser-health-component.js';

// Create application instances when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
  // Initialize the event manager application
  window.eventManagerApp = new EventManagerApp();
  window.eventManagerApp.init();

  // Initialize the parser health component
  window.parserHealthComponent = new ParserHealthComponent();
  window.parserHealthComponent.init();
});

// Make updateActionButtons available globally for inline handlers
window.updateActionButtons = function() {
  if (window.eventManagerApp) {
    window.eventManagerApp.updateActionButtons();
  }
};