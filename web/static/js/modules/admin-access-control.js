/**
 * Manages admin-only content visibility
 */
export class AdminAccessManager {
  constructor() {
    this.isAdminMode = false;
    this.adminElements = [];
  }

  /**
   * Initialize admin access management
   */
  init() {
    // Find all admin-only elements
    this.adminElements = Array.from(document.querySelectorAll('[data-admin-only]'));

    // Check admin status on page load
    this.checkAdminAccess();

    // Set up event listener for potential dynamic changes
    window.addEventListener('popstate', () => this.checkAdminAccess());
  }

  /**
   * Check and apply admin access
   */
  checkAdminAccess() {
    const urlParams = new URLSearchParams(window.location.search);
    this.isAdminMode = urlParams.get('admin') !== null;

    // Toggle visibility of admin-only elements
    this.adminElements.forEach(element => {
      if (this.isAdminMode) {
        element.classList.remove('d-none');
      } else {
        element.classList.add('d-none');
      }
    });

    // Optional: Add a visual indicator of admin mode
    this.updateAdminIndicator();
  }

  /**
   * Add a visual indicator when in admin mode
   */
  updateAdminIndicator() {
    let adminBadge = document.getElementById('admin-mode-badge');

    if (this.isAdminMode) {
      if (!adminBadge) {
        adminBadge = document.createElement('span');
        adminBadge.id = 'admin-mode-badge';
        adminBadge.className = 'badge bg-danger position-fixed top-0 end-0 m-3 z-3';
        adminBadge.textContent = 'ADMIN MODE';
        document.body.appendChild(adminBadge);
      }
    } else if (adminBadge) {
      adminBadge.remove();
    }
  }
}