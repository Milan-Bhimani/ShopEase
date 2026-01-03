/**
 * ==============================================================================
 * E-Commerce Frontend Utilities (utils.js)
 * ==============================================================================
 *
 * PURPOSE:
 * --------
 * This module provides reusable utility functions for the frontend.
 * These functions handle common tasks across all pages:
 * - Price and date formatting (Indian locale)
 * - Toast notifications for user feedback
 * - Loading states and skeleton screens
 * - Product card rendering
 * - Navigation and authentication UI
 * - Input validation
 * - Order status display
 *
 * ARCHITECTURE:
 * -------------
 * Functions are organized by category:
 *
 * FORMATTING:
 *   - formatPrice(): INR currency formatting
 *   - formatDate(): Indian date format
 *   - truncateText(): Text ellipsis
 *
 * UI COMPONENTS:
 *   - showToast(): Notification alerts
 *   - showLoading(): Loading spinners
 *   - createProductCard(): Product grid cards
 *   - createSkeletonCards(): Loading placeholders
 *   - getStatusBadge(): Order status badges
 *
 * NAVIGATION:
 *   - updateNavbar(): Auth-aware navbar
 *   - updateCartBadge(): Cart item count
 *   - handleLogout(): Logout flow
 *   - requireAuth(): Protected page guard
 *
 * VALIDATION:
 *   - isValidEmail(): Email format check
 *   - isValidPhone(): Phone number check
 *   - isValidPincode(): Postal code check
 *
 * HELPERS:
 *   - getUrlParam(): Query string parsing
 *   - debounce(): Function rate limiting
 *   - getPaymentMethodName(): Payment display names
 *
 * DEPENDENCIES:
 * -------------
 * - api.js must be loaded first (for API.isAuthenticated, API.Cart, etc.)
 * - Bootstrap 5 (for alert, badge, spinner classes)
 * - Bootstrap Icons (for star icon in ratings)
 *
 * USAGE:
 * ------
 *   // Price formatting
 *   formatPrice(1999);  // "₹1,999"
 *
 *   // Show notification
 *   showToast('Item added to cart', 'success');
 *
 *   // Protect page
 *   if (!requireAuth()) return;  // Redirects to login
 *
 *   // All utilities also available via window.Utils
 *   Utils.showToast('Hello');
 */

// ==============================================================================
// FORMATTING UTILITIES
// ==============================================================================

/**
 * Format price in Indian Rupees (INR)
 *
 * Uses Intl.NumberFormat for proper Indian number formatting:
 * - Indian numbering system (lakhs, crores)
 * - Rupee symbol (₹)
 * - No decimal places (common for Indian e-commerce)
 *
 * Examples:
 *   formatPrice(1999)     -> "₹1,999"
 *   formatPrice(150000)   -> "₹1,50,000"
 *   formatPrice(10000000) -> "₹1,00,00,000"
 *
 * @param {number} price - Price in rupees
 * @returns {string} Formatted price string with ₹ symbol
 */
function formatPrice(price) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
    }).format(price);
}

/**
 * Format date in Indian locale
 *
 * Converts ISO date strings to human-readable format.
 * Uses short month names for compact display.
 *
 * Examples:
 *   formatDate("2024-01-15T10:30:00") -> "15 Jan 2024"
 *   formatDate("2024-12-25")          -> "25 Dec 2024"
 *   formatDate(null)                  -> ""
 *
 * @param {string} dateString - ISO date string or Date-compatible string
 * @returns {string} Formatted date or empty string if invalid
 */
function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-IN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
    });
}

// ==============================================================================
// UI COMPONENT UTILITIES
// ==============================================================================

/**
 * Show floating toast notification
 *
 * Creates a Bootstrap alert that appears at the top of the screen.
 * Auto-dismisses after 5 seconds with fade animation.
 * Only one toast is shown at a time (removes existing toasts first).
 *
 * Alert Types:
 *   - 'success' (default): Green alert for positive actions
 *   - 'error': Red alert for failures
 *   - 'warning': Yellow alert for cautions
 *
 * CSS Required:
 *   .alert-floating {
 *     position: fixed;
 *     top: 80px;
 *     left: 50%;
 *     transform: translateX(-50%);
 *     z-index: 1050;
 *   }
 *
 * Usage:
 *   showToast('Item added to cart');              // Success
 *   showToast('Failed to add item', 'error');     // Error
 *   showToast('Low stock warning', 'warning');    // Warning
 *
 * @param {string} message - Message to display
 * @param {string} type - Alert type: 'success', 'error', or 'warning'
 */
function showToast(message, type = 'success') {
    // Remove existing toasts
    document.querySelectorAll('.alert-floating').forEach(el => el.remove());

    const alertClass = type === 'error' ? 'alert-danger' :
                      type === 'warning' ? 'alert-warning' : 'alert-success';

    const toast = document.createElement('div');
    toast.className = `alert ${alertClass} alert-floating alert-dismissible fade show`;
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    document.body.appendChild(toast);

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 150);
    }, 5000);
}

/**
 * Show loading spinner inside a container
 *
 * Replaces container content with a centered Bootstrap spinner.
 * Use this when loading data for a specific section of the page.
 *
 * The container's content is completely replaced, so any
 * existing content will be lost. Save it first if needed.
 *
 * CSS Required:
 *   .loading-spinner {
 *     display: flex;
 *     justify-content: center;
 *     padding: 2rem;
 *   }
 *
 * Usage:
 *   const container = document.getElementById('products-grid');
 *   showLoading(container);
 *   const products = await API.Products.getProducts();
 *   container.innerHTML = products.map(createProductCard).join('');
 *
 * @param {HTMLElement} container - DOM element to show spinner in
 */
function showLoading(container) {
    container.innerHTML = `
        <div class="loading-spinner">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        </div>
    `;
}

/**
 * Create product card HTML for grid display
 *
 * Generates a Bootstrap card for a product with:
 * - Thumbnail image (with fallback placeholder)
 * - Product name
 * - Rating stars (if available)
 * - Price with original price strikethrough
 * - Discount percentage badge
 * - Out of stock indicator
 *
 * The entire card is clickable and navigates to the product detail page.
 *
 * Responsive Grid:
 *   - 2 columns on mobile (col-6)
 *   - 3 columns on tablet (col-md-4)
 *   - 4 columns on desktop (col-lg-3)
 *
 * Image Handling:
 *   - Uses product.thumbnail first, then first image from product.images
 *   - Falls back to placeholder if no images
 *   - Uses lazy loading (loading="lazy")
 *   - Has onerror handler for broken images
 *
 * Usage:
 *   const products = await API.Products.getProducts();
 *   const html = products.map(createProductCard).join('');
 *   document.getElementById('product-grid').innerHTML = html;
 *
 * @param {Object} product - Product object from API
 * @param {string} product.id - Product ID for link
 * @param {string} product.name - Product name
 * @param {number} product.price - Current price
 * @param {number} [product.original_price] - Original price before discount
 * @param {number} [product.discount_percentage] - Discount percentage
 * @param {number} [product.rating] - Average rating (1-5)
 * @param {number} [product.review_count] - Number of reviews
 * @param {boolean} product.in_stock - Stock availability
 * @param {string} [product.thumbnail] - Thumbnail image URL
 * @param {string[]} [product.images] - Array of image URLs
 * @returns {string} HTML string for the product card
 */
function createProductCard(product) {
    const discount = product.discount_percentage;
    const thumbnail = product.thumbnail || product.images?.[0] || 'https://via.placeholder.com/200x200?text=No+Image';

    return `
        <div class="col-6 col-md-4 col-lg-3 mb-4">
            <div class="product-card card h-100" onclick="window.location.href='/product.html?id=${product.id}'">
                <img src="${thumbnail}" class="card-img-top" alt="${product.name}"
                     loading="lazy"
                     onerror="this.src='https://via.placeholder.com/200x200?text=No+Image'">
                <div class="card-body">
                    <h6 class="product-title">${product.name}</h6>
                    ${product.rating ? `
                        <span class="rating mb-2">
                            ${product.rating.toFixed(1)} <i class="bi bi-star-fill"></i>
                        </span>
                        <span class="text-muted small ms-1">(${product.review_count || 0})</span>
                    ` : ''}
                    <div class="mt-2">
                        <span class="product-price">${formatPrice(product.price)}</span>
                        ${product.original_price ? `
                            <span class="original-price">${formatPrice(product.original_price)}</span>
                        ` : ''}
                        ${discount ? `
                            <span class="discount-badge ms-2">${discount}% off</span>
                        ` : ''}
                    </div>
                    ${!product.in_stock ? '<div class="text-danger small mt-1">Out of Stock</div>' : ''}
                </div>
            </div>
        </div>
    `;
}

/**
 * Create skeleton loading cards for product grid
 *
 * Generates placeholder cards that mimic the layout of product cards.
 * Used for "skeleton loading" pattern - shows the UI structure while
 * actual data is being fetched.
 *
 * This provides better UX than a spinner because:
 * - User sees the expected layout immediately
 * - Reduces perceived loading time
 * - No layout shift when content loads
 *
 * CSS Required:
 *   .skeleton {
 *     background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
 *     background-size: 200% 100%;
 *     animation: shimmer 1.5s infinite;
 *   }
 *
 * Usage:
 *   // Show skeletons while loading
 *   container.innerHTML = createSkeletonCards(8);
 *
 *   // Replace with actual products
 *   const products = await API.Products.getProducts();
 *   container.innerHTML = products.map(createProductCard).join('');
 *
 * @param {number} count - Number of skeleton cards to create (default: 8)
 * @returns {string} HTML string with skeleton cards
 */
function createSkeletonCards(count = 8) {
    let html = '';
    for (let i = 0; i < count; i++) {
        html += `
            <div class="col-6 col-md-4 col-lg-3 mb-4">
                <div class="card h-100">
                    <div class="skeleton" style="height: 200px;"></div>
                    <div class="card-body">
                        <div class="skeleton mb-2" style="height: 20px;"></div>
                        <div class="skeleton mb-2" style="height: 20px; width: 60%;"></div>
                        <div class="skeleton" style="height: 24px; width: 40%;"></div>
                    </div>
                </div>
            </div>
        `;
    }
    return html;
}

// ==============================================================================
// NAVIGATION UTILITIES
// ==============================================================================

/**
 * Update cart item count badge in navbar
 *
 * Fetches the current cart summary from the API and updates
 * the badge number next to the cart icon.
 *
 * Behavior:
 * - If not authenticated: Shows 0, hides badge
 * - If cart is empty: Hides badge
 * - If cart has items: Shows count, displays badge
 *
 * This function is called:
 * - On page load (via updateNavbar)
 * - After adding/removing cart items
 * - After login/logout
 *
 * HTML Expected:
 *   <span id="cart-badge" class="badge bg-danger">0</span>
 *
 * @async
 */
async function updateCartBadge() {
    const badge = document.getElementById('cart-badge');
    if (!badge) return;

    if (!API.isAuthenticated()) {
        badge.textContent = '0';
        badge.style.display = 'none';
        return;
    }

    try {
        const summary = await API.Cart.getSummary();
        badge.textContent = summary.item_count || 0;
        badge.style.display = summary.item_count > 0 ? 'inline-block' : 'none';
    } catch (error) {
        badge.textContent = '0';
        badge.style.display = 'none';
    }
}

/**
 * Update navbar UI based on authentication state
 *
 * Toggles between two navbar states:
 *
 * 1. LOGGED OUT:
 *    - Shows "Login" and "Sign Up" buttons (auth-buttons)
 *    - Hides user dropdown menu (user-menu)
 *
 * 2. LOGGED IN:
 *    - Hides login/signup buttons
 *    - Shows user dropdown with name (user-menu)
 *    - Updates cart badge count
 *
 * HTML Expected:
 *   <div id="auth-buttons">
 *     <a href="/login.html">Login</a>
 *     <a href="/signup.html">Sign Up</a>
 *   </div>
 *   <div id="user-menu" style="display: none;">
 *     <span id="user-name"></span>
 *     <a onclick="handleLogout()">Logout</a>
 *   </div>
 *
 * Called automatically on DOMContentLoaded via the init at bottom of file.
 */
function updateNavbar() {
    const authButtons = document.getElementById('auth-buttons');
    const userMenu = document.getElementById('user-menu');
    const userNameSpan = document.getElementById('user-name');

    if (!authButtons || !userMenu) return;

    if (API.isAuthenticated()) {
        const user = API.getCurrentUser();
        authButtons.style.display = 'none';
        userMenu.style.display = 'block';
        if (userNameSpan && user) {
            userNameSpan.textContent = user.first_name || 'User';
        }
        updateCartBadge();

        // Add Admin Dashboard link if user is admin
        if (user && user.is_admin) {
            addAdminLink();
        }
    } else {
        authButtons.style.display = 'block';
        userMenu.style.display = 'none';
    }
}

/**
 * Add Admin Dashboard link to navbar for admin users
 *
 * Dynamically inserts an "Admin Dashboard" link in the user dropdown menu
 * if the current user has admin privileges. The link is added after
 * "Orders" and before the divider.
 *
 * Only adds the link if it doesn't already exist (prevents duplicates
 * on multiple calls to updateNavbar).
 */
function addAdminLink() {
    const userMenu = document.getElementById('user-menu');
    if (!userMenu) return;

    // Check if admin link already exists
    if (document.getElementById('admin-dashboard-link')) return;

    const dropdownMenu = userMenu.querySelector('.dropdown-menu');
    if (!dropdownMenu) return;

    // Find the divider's parent li to insert before it
    const dividerLi = dropdownMenu.querySelector('li:has(.dropdown-divider)');
    if (dividerLi) {
        // Create admin link li
        const adminLi = document.createElement('li');
        adminLi.id = 'admin-dashboard-link';
        adminLi.innerHTML = '<a class="dropdown-item text-primary fw-semibold" href="/admin.html"><i class="bi bi-speedometer2 me-2"></i>Admin Dashboard</a>';

        // Insert before the divider li
        dropdownMenu.insertBefore(adminLi, dividerLi);
    }
}

/**
 * Handle user logout
 *
 * Performs a complete logout:
 * 1. Calls API to invalidate server-side session
 * 2. Clears local storage (token, user data)
 * 3. Shows success toast
 * 4. Redirects to login page
 *
 * The API call failure is silently ignored because:
 * - Local logout should still happen even if API fails
 * - Server tokens expire anyway
 * - User expects to be logged out regardless
 *
 * Usage:
 *   <button onclick="handleLogout()">Logout</button>
 *   // Or: Utils.handleLogout()
 *
 * @async
 */
async function handleLogout() {
    try {
        await API.Auth.logout();
        showToast('Logged out successfully');
        window.location.href = '/login.html';
    } catch (error) {
        showToast('Error logging out', 'error');
    }
}

/**
 * Require authentication - redirect to login if not authenticated
 *
 * Use this as a guard at the start of protected page scripts.
 * If user is not logged in, redirects to login with return URL.
 *
 * Return URL Handling:
 * - Current page URL is encoded and passed as ?return= parameter
 * - After successful login, user is redirected back to original page
 *
 * Usage (at start of protected page):
 *   document.addEventListener('DOMContentLoaded', () => {
 *       if (!requireAuth()) return;  // Exits if not logged in
 *       loadProfileData();           // Only runs if logged in
 *   });
 *
 * @returns {boolean} true if authenticated, false if redirecting to login
 */
function requireAuth() {
    if (!API.isAuthenticated()) {
        const returnUrl = encodeURIComponent(window.location.pathname + window.location.search);
        window.location.href = `/login.html?return=${returnUrl}`;
        return false;
    }
    return true;
}

// ==============================================================================
// HELPER UTILITIES
// ==============================================================================

/**
 * Get URL query parameter value
 *
 * Parses the current page URL's query string and returns
 * the value of the specified parameter.
 *
 * Examples:
 *   // URL: /product.html?id=123&color=blue
 *   getUrlParam('id')     // "123"
 *   getUrlParam('color')  // "blue"
 *   getUrlParam('size')   // null
 *
 * Usage:
 *   const productId = getUrlParam('id');
 *   if (productId) {
 *       loadProduct(productId);
 *   }
 *
 * @param {string} param - Parameter name to look for
 * @returns {string|null} Parameter value or null if not found
 */
function getUrlParam(param) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(param);
}

/**
 * Debounce function - limits how often a function can fire
 *
 * Returns a new function that delays calling the original function
 * until after `wait` milliseconds have passed since the last call.
 *
 * Common Use Cases:
 * - Search input: Wait for user to stop typing before searching
 * - Window resize: Wait for resize to finish before recalculating
 * - Scroll events: Limit expensive scroll handlers
 *
 * How it works:
 * 1. Function is called
 * 2. Timer starts for `wait` ms
 * 3. If called again before timer expires, reset timer
 * 4. When timer expires, execute the function once
 *
 * Usage:
 *   const searchInput = document.getElementById('search');
 *   const debouncedSearch = debounce(performSearch, 300);
 *   searchInput.addEventListener('input', debouncedSearch);
 *
 *   // performSearch will only run 300ms after user stops typing
 *
 * @param {Function} func - Function to debounce
 * @param {number} wait - Delay in milliseconds
 * @returns {Function} Debounced function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// ==============================================================================
// VALIDATION UTILITIES
// ==============================================================================

/**
 * Validate email format
 *
 * Basic email validation using regex pattern.
 * Checks for: something@something.something
 *
 * This is a client-side convenience check only.
 * The backend uses Pydantic EmailStr for proper validation.
 *
 * @param {string} email - Email address to validate
 * @returns {boolean} true if format is valid
 */
function isValidEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

/**
 * Validate phone number format
 *
 * Accepts various formats:
 * - 9876543210 (plain 10 digits)
 * - +91 9876543210 (with country code)
 * - 987-654-3210 (with dashes)
 *
 * Cleans spaces and dashes, then checks for 10-15 digits.
 * Matches backend validation in validators.py.
 *
 * @param {string} phone - Phone number to validate
 * @returns {boolean} true if format is valid
 */
function isValidPhone(phone) {
    const cleaned = phone.replace(/[\s\-]/g, '');
    return /^\+?\d{10,15}$/.test(cleaned);
}

/**
 * Validate Indian pincode format
 *
 * Indian pincodes are 6 digits.
 * Accepts 5-10 digits to support international postal codes.
 * Matches backend validation in validators.py.
 *
 * @param {string} pincode - Postal code to validate
 * @returns {boolean} true if format is valid
 */
function isValidPincode(pincode) {
    return /^\d{5,10}$/.test(pincode.trim());
}

/**
 * Truncate text with ellipsis
 *
 * Shortens text to maximum length and adds "..." if truncated.
 * Useful for product descriptions, addresses, etc.
 *
 * Examples:
 *   truncateText("Short", 10)      // "Short"
 *   truncateText("Long text here", 8)  // "Long tex..."
 *
 * @param {string} text - Text to truncate
 * @param {number} maxLength - Maximum characters before truncation
 * @returns {string} Truncated text with ellipsis if needed
 */
function truncateText(text, maxLength) {
    if (text.length <= maxLength) return text;
    return text.substr(0, maxLength) + '...';
}

// ==============================================================================
// ORDER STATUS UTILITIES
// ==============================================================================

/**
 * Get Bootstrap badge HTML for order status
 *
 * Returns a colored badge based on order lifecycle stage.
 * Colors follow common UX conventions:
 *   - Warning (yellow): Pending, needs action
 *   - Info (blue): Confirmed, Out for Delivery
 *   - Primary (dark blue): Processing, Shipped
 *   - Success (green): Delivered
 *   - Danger (red): Cancelled
 *   - Secondary (gray): Returned, Refunded
 *
 * Order Lifecycle:
 *   pending → confirmed → processing → shipped → out_for_delivery → delivered
 *                                                                 ↘ cancelled
 *                                                                 ↘ returned → refunded
 *
 * Usage:
 *   const badgeHtml = getStatusBadge('shipped');
 *   // Returns: <span class="badge bg-primary">Shipped</span>
 *
 * @param {string} status - Order status from backend
 * @returns {string} HTML string with Bootstrap badge
 */
function getStatusBadge(status) {
    const statusMap = {
        'pending': { class: 'bg-warning', text: 'Pending' },
        'confirmed': { class: 'bg-info', text: 'Confirmed' },
        'processing': { class: 'bg-primary', text: 'Processing' },
        'shipped': { class: 'bg-primary', text: 'Shipped' },
        'out_for_delivery': { class: 'bg-info', text: 'Out for Delivery' },
        'delivered': { class: 'bg-success', text: 'Delivered' },
        'cancelled': { class: 'bg-danger', text: 'Cancelled' },
        'returned': { class: 'bg-secondary', text: 'Returned' },
        'refunded': { class: 'bg-secondary', text: 'Refunded' },
    };

    const statusInfo = statusMap[status] || { class: 'bg-secondary', text: status };
    return `<span class="badge ${statusInfo.class}">${statusInfo.text}</span>`;
}

/**
 * Get human-readable payment method name
 *
 * Converts internal payment method codes to display names.
 * These match the payment methods supported by the backend.
 *
 * Supported Methods:
 *   - card: Credit/Debit Card (Visa, Mastercard, etc.)
 *   - upi: UPI (Google Pay, PhonePe, Paytm, etc.)
 *   - net_banking: Net Banking (bank transfers)
 *   - wallet: Digital Wallets (Paytm, Amazon Pay, etc.)
 *   - cod: Cash on Delivery
 *
 * Note: Payment is simulated - no real gateway integration.
 *
 * @param {string} method - Payment method code from backend
 * @returns {string} Human-readable payment method name
 */
function getPaymentMethodName(method) {
    const methods = {
        'card': 'Credit/Debit Card',
        'upi': 'UPI',
        'net_banking': 'Net Banking',
        'wallet': 'Wallet',
        'cod': 'Cash on Delivery',
    };
    return methods[method] || method;
}

// ==============================================================================
// INITIALIZATION
// ==============================================================================

/**
 * Auto-initialize on page load
 *
 * Updates the navbar to reflect current authentication state.
 * This runs on every page that includes utils.js.
 *
 * Load Order:
 * 1. api.js (defines API object with isAuthenticated, getCurrentUser)
 * 2. utils.js (uses API object, runs updateNavbar on load)
 * 3. Page-specific JS (e.g., cart.js, profile.js)
 */
document.addEventListener('DOMContentLoaded', () => {
    updateNavbar();
});

// ==============================================================================
// EXPORTS
// ==============================================================================

/**
 * Export all utilities to window.Utils
 *
 * This makes all functions available globally via the Utils namespace.
 * Functions are also available directly (formatPrice, showToast, etc.)
 * but Utils.* is useful when you need to reference from inline handlers.
 *
 * Example:
 *   <button onclick="Utils.handleLogout()">Logout</button>
 *   <script>Utils.showToast('Hello');</script>
 */
window.Utils = {
    formatPrice,
    formatDate,
    showToast,
    showLoading,
    createProductCard,
    createSkeletonCards,
    updateCartBadge,
    updateNavbar,
    handleLogout,
    requireAuth,
    getUrlParam,
    debounce,
    isValidEmail,
    isValidPhone,
    isValidPincode,
    truncateText,
    getStatusBadge,
    getPaymentMethodName,
};
