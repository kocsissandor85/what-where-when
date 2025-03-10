import { EventManagerApp } from './modules/app.js';
import { ParserHealthComponent } from './modules/parser-health-component.js';
import { TagMappingUIManager } from './modules/tag-mapping-ui-manager.js';
import { AdminAccessManager } from './modules/admin-access-control.js';

function checkAdminAccess() {
  const urlParams = new URLSearchParams(window.location.search);
  const isAdmin = urlParams.get('admin') !== null;

  const adminSection = document.getEleme('adminSection');
  if (isAdmin) {
    adminSection.classList.remove('d-none');
  } else {
    adminSection.classList.add('d-none');
  }
}

// Create application instances when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
  // Initialize the event manager application
  window.eventManagerApp = new EventManagerApp();
  window.eventManagerApp.init();

  // Initialize the parser health component
  window.parserHealthComponent = new ParserHealthComponent();
  window.parserHealthComponent.init();

  // Initialize the tag mapping UI manager
  window.tagMappingUIManager = new TagMappingUIManager();
  window.tagMappingUIManager.loadTagMappings();

  // Initialize admin access management when DOM is loaded
  window.adminAccessManager = new AdminAccessManager();
  window.adminAccessManager.init();
});

// Make updateActionButtons available globally for inline handlers
window.updateActionButtons = function() {
  if (window.eventManagerApp) {
    window.eventManagerApp.updateActionButtons();
  }
};