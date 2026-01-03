/**
 * Utility functions for the e-commerce frontend
 */

/**
 * Format price in INR
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
 * Format date
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

/**
 * Show toast notification
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
 * Show loading spinner
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
 * Create product card HTML
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
 * Create skeleton loading cards
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

/**
 * Update cart badge in navbar
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
 * Update navbar based on auth state
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
    } else {
        authButtons.style.display = 'block';
        userMenu.style.display = 'none';
    }
}

/**
 * Handle logout
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
 */
function requireAuth() {
    if (!API.isAuthenticated()) {
        const returnUrl = encodeURIComponent(window.location.pathname + window.location.search);
        window.location.href = `/login.html?return=${returnUrl}`;
        return false;
    }
    return true;
}

/**
 * Get URL parameter
 */
function getUrlParam(param) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(param);
}

/**
 * Debounce function
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

/**
 * Validate email format
 */
function isValidEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

/**
 * Validate phone number
 */
function isValidPhone(phone) {
    const cleaned = phone.replace(/[\s\-]/g, '');
    return /^\+?\d{10,15}$/.test(cleaned);
}

/**
 * Validate pincode
 */
function isValidPincode(pincode) {
    return /^\d{5,10}$/.test(pincode.trim());
}

/**
 * Truncate text
 */
function truncateText(text, maxLength) {
    if (text.length <= maxLength) return text;
    return text.substr(0, maxLength) + '...';
}

/**
 * Get order status badge
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
 * Get payment method display name
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

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    updateNavbar();
});

// Export utilities
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
