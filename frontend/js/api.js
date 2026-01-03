/**
 * ==============================================================================
 * E-Commerce API Client (api.js)
 * ==============================================================================
 *
 * PURPOSE:
 * --------
 * This module handles all communication between the frontend and backend API.
 * It provides a clean interface for making API calls with:
 * - Automatic authentication header injection
 * - Error handling and 401 redirects
 * - Response caching for performance
 * - Consistent JSON request/response handling
 *
 * ARCHITECTURE:
 * -------------
 * The module is organized into domain-specific API objects:
 * - AuthAPI: Login, register, logout, OTP
 * - UsersAPI: Profile management
 * - ProductsAPI: Product listing and details
 * - CartAPI: Shopping cart operations
 * - AddressesAPI: Shipping address CRUD
 * - OrdersAPI: Order placement and tracking
 *
 * All exposed via window.API for use in other scripts.
 *
 * AUTHENTICATION:
 * ---------------
 * JWT token is stored in localStorage and automatically
 * added to request headers as: Authorization: Bearer <token>
 *
 * On 401 Unauthorized:
 * - Token and user data are cleared
 * - User is redirected to login page
 * - Original URL is preserved for redirect back
 *
 * CACHING:
 * --------
 * GET requests for products and categories are cached for 5 minutes.
 * This reduces API calls and improves performance.
 * Cache is stored in memory (lost on page refresh).
 *
 * USAGE:
 * ------
 *   // Check authentication
 *   if (API.isAuthenticated()) { ... }
 *
 *   // Login
 *   const result = await API.Auth.login(email, password);
 *
 *   // Get products
 *   const products = await API.Products.getProducts({ category: 'Electronics' });
 *
 *   // Add to cart
 *   await API.Cart.addItem(productId, quantity);
 */

// ==============================================================================
// CONFIGURATION
// ==============================================================================

// API Base URL - nginx proxy routes /api to backend
// In production on Vercel, this would be the same origin
const API_BASE_URL = '/api';

// ==============================================================================
// AUTHENTICATION STATE
// ==============================================================================

// JWT token persisted in localStorage
// Loaded on page load, cleared on logout
let authToken = localStorage.getItem('authToken');

// Current user object (cached from login response)
// Contains: id, email, first_name, last_name, phone
let currentUser = JSON.parse(localStorage.getItem('currentUser') || 'null');

// ==============================================================================
// RESPONSE CACHING
// ==============================================================================

// Simple in-memory cache for GET requests
// Reduces API calls for frequently accessed data
const apiCache = new Map();

// Cache time-to-live: 5 minutes
// After this, cached data is considered stale
const CACHE_TTL = 5 * 60 * 1000;

/**
 * Get cached data if still valid
 * @param {string} key - Cache key
 * @returns {any|null} - Cached data or null if expired/missing
 */
function getCached(key) {
    const cached = apiCache.get(key);
    if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
        return cached.data;
    }
    // Remove expired cache entry
    apiCache.delete(key);
    return null;
}

/**
 * Store data in cache with timestamp
 * @param {string} key - Cache key
 * @param {any} data - Data to cache
 */
function setCache(key, data) {
    apiCache.set(key, { data, timestamp: Date.now() });
}

/**
 * Clear all cached data
 * Called on logout or when data might be stale
 */
function clearCache() {
    apiCache.clear();
}

/**
 * Make an API request
 */
async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;

    const headers = {
        'Content-Type': 'application/json',
        ...options.headers,
    };

    if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
    }

    try {
        const response = await fetch(url, {
            ...options,
            headers,
        });

        // Handle 401 Unauthorized
        if (response.status === 401) {
            // Don't redirect for auth endpoints (login, pre-login)
            if (!endpoint.startsWith('/auth/')) {
                clearAuth();
                if (!window.location.pathname.includes('login')) {
                    window.location.href = '/login.html';
                }
            }
            // Let the error fall through to be handled by caller
        }

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'An error occurred');
        }

        return data;
    } catch (error) {
        if (error.name === 'TypeError' && error.message === 'Failed to fetch') {
            throw new Error('Unable to connect to server. Please check your connection.');
        }
        throw error;
    }
}

/**
 * Set authentication data
 */
function setAuth(token, user) {
    authToken = token;
    currentUser = user;
    localStorage.setItem('authToken', token);
    localStorage.setItem('currentUser', JSON.stringify(user));
}

/**
 * Clear authentication data
 */
function clearAuth() {
    authToken = null;
    currentUser = null;
    localStorage.removeItem('authToken');
    localStorage.removeItem('currentUser');
}

/**
 * Check if user is authenticated
 */
function isAuthenticated() {
    return !!authToken;
}

/**
 * Get current user
 */
function getCurrentUser() {
    return currentUser;
}

// ============================================================
// Authentication API
// ============================================================

const AuthAPI = {
    /**
     * Register a new user
     */
    async register(userData) {
        const response = await apiRequest('/auth/register', {
            method: 'POST',
            body: JSON.stringify(userData),
        });
        setAuth(response.access_token, response.user);
        return response;
    },

    /**
     * Pre-login check - verify credentials and check if OTP is required
     */
    async preLogin(email, password) {
        return apiRequest('/auth/pre-login', {
            method: 'POST',
            body: JSON.stringify({ email, password }),
        });
    },

    /**
     * Login user
     */
    async login(email, password) {
        const response = await apiRequest('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password }),
        });
        setAuth(response.access_token, response.user);
        return response;
    },

    /**
     * Logout user
     */
    async logout() {
        try {
            await apiRequest('/auth/logout', { method: 'POST' });
        } catch (e) {
            // Ignore logout errors
        }
        clearAuth();
    },

    /**
     * Get current user profile
     */
    async getProfile() {
        return apiRequest('/auth/me');
    },

    /**
     * Refresh token
     */
    async refreshToken() {
        const response = await apiRequest('/auth/refresh', { method: 'POST' });
        setAuth(response.access_token, response.user);
        return response;
    },

    /**
     * Send OTP for email verification
     */
    async sendOTP(email, purpose) {
        return apiRequest('/auth/otp/send', {
            method: 'POST',
            body: JSON.stringify({ email, purpose }),
        });
    },

    /**
     * Verify OTP
     */
    async verifyOTP(email, otp, purpose) {
        return apiRequest('/auth/otp/verify', {
            method: 'POST',
            body: JSON.stringify({ email, otp, purpose }),
        });
    },

    /**
     * Resend OTP
     */
    async resendOTP(email, purpose) {
        return apiRequest('/auth/otp/resend', {
            method: 'POST',
            body: JSON.stringify({ email, purpose }),
        });
    },

    /**
     * Login with OTP (passwordless login)
     */
    async loginWithOTP(email, otp) {
        const response = await apiRequest('/auth/login-otp', {
            method: 'POST',
            body: JSON.stringify({ email, otp }),
        });
        setAuth(response.access_token, response.user);
        return response;
    },
};

// ============================================================
// Users API
// ============================================================

const UsersAPI = {
    /**
     * Get user profile
     */
    async getProfile() {
        return apiRequest('/users/profile');
    },

    /**
     * Update user profile
     */
    async updateProfile(data) {
        const response = await apiRequest('/users/profile', {
            method: 'PUT',
            body: JSON.stringify(data),
        });
        currentUser = { ...currentUser, ...response };
        localStorage.setItem('currentUser', JSON.stringify(currentUser));
        return response;
    },

    /**
     * Change password
     */
    async changePassword(currentPassword, newPassword) {
        return apiRequest('/users/change-password', {
            method: 'POST',
            body: JSON.stringify({
                current_password: currentPassword,
                new_password: newPassword,
            }),
        });
    },
};

// ============================================================
// Products API
// ============================================================

const ProductsAPI = {
    /**
     * Get all products with optional filters
     */
    async getProducts(params = {}) {
        const queryParams = new URLSearchParams();

        if (params.category) queryParams.set('category', params.category);
        if (params.search) queryParams.set('search', params.search);
        if (params.featured) queryParams.set('featured', 'true');
        if (params.minPrice) queryParams.set('min_price', params.minPrice);
        if (params.maxPrice) queryParams.set('max_price', params.maxPrice);
        if (params.page) queryParams.set('page', params.page);
        if (params.perPage) queryParams.set('per_page', params.perPage);

        const query = queryParams.toString();
        return apiRequest(`/products${query ? '?' + query : ''}`);
    },

    /**
     * Get featured products (cached)
     */
    async getFeatured(limit = 10) {
        const cacheKey = `featured_${limit}`;
        const cached = getCached(cacheKey);
        if (cached) return cached;

        const data = await apiRequest(`/products/featured?limit=${limit}`);
        setCache(cacheKey, data);
        return data;
    },

    /**
     * Get product categories (cached)
     */
    async getCategories() {
        const cacheKey = 'categories';
        const cached = getCached(cacheKey);
        if (cached) return cached;

        const data = await apiRequest('/products/categories');
        setCache(cacheKey, data);
        return data;
    },

    /**
     * Get single product by ID (cached)
     */
    async getProduct(productId) {
        const cacheKey = `product_${productId}`;
        const cached = getCached(cacheKey);
        if (cached) return cached;

        const data = await apiRequest(`/products/${productId}`);
        setCache(cacheKey, data);
        return data;
    },
};

// ============================================================
// Cart API
// ============================================================

const CartAPI = {
    /**
     * Get cart
     */
    async getCart() {
        return apiRequest('/cart');
    },

    /**
     * Get cart summary (for header)
     */
    async getSummary() {
        return apiRequest('/cart/summary');
    },

    /**
     * Add item to cart
     */
    async addItem(productId, quantity = 1) {
        return apiRequest('/cart/items', {
            method: 'POST',
            body: JSON.stringify({ product_id: productId, quantity }),
        });
    },

    /**
     * Update item quantity
     */
    async updateItem(productId, quantity) {
        return apiRequest(`/cart/items/${productId}`, {
            method: 'PUT',
            body: JSON.stringify({ quantity }),
        });
    },

    /**
     * Remove item from cart
     */
    async removeItem(productId) {
        return apiRequest(`/cart/items/${productId}`, {
            method: 'DELETE',
        });
    },

    /**
     * Clear cart
     */
    async clear() {
        return apiRequest('/cart', { method: 'DELETE' });
    },
};

// ============================================================
// Addresses API
// ============================================================

const AddressesAPI = {
    /**
     * Get all addresses
     */
    async getAddresses() {
        return apiRequest('/addresses');
    },

    /**
     * Get default address
     */
    async getDefault() {
        return apiRequest('/addresses/default');
    },

    /**
     * Get address by ID
     */
    async getAddress(addressId) {
        return apiRequest(`/addresses/${addressId}`);
    },

    /**
     * Create new address
     */
    async create(addressData) {
        return apiRequest('/addresses', {
            method: 'POST',
            body: JSON.stringify(addressData),
        });
    },

    /**
     * Update address
     */
    async update(addressId, addressData) {
        return apiRequest(`/addresses/${addressId}`, {
            method: 'PUT',
            body: JSON.stringify(addressData),
        });
    },

    /**
     * Delete address
     */
    async delete(addressId) {
        return apiRequest(`/addresses/${addressId}`, {
            method: 'DELETE',
        });
    },

    /**
     * Set as default
     */
    async setDefault(addressId) {
        return apiRequest(`/addresses/${addressId}/set-default`, {
            method: 'POST',
        });
    },
};

// ============================================================
// Orders API
// ============================================================

const OrdersAPI = {
    /**
     * Get all orders
     */
    async getOrders(page = 1, perPage = 10) {
        return apiRequest(`/orders?page=${page}&per_page=${perPage}`);
    },

    /**
     * Get order by ID
     */
    async getOrder(orderId) {
        return apiRequest(`/orders/${orderId}`);
    },

    /**
     * Create order
     */
    async create(orderData) {
        return apiRequest('/orders', {
            method: 'POST',
            body: JSON.stringify(orderData),
        });
    },

    /**
     * Cancel order
     */
    async cancel(orderId) {
        return apiRequest(`/orders/${orderId}/cancel`, {
            method: 'POST',
        });
    },

    /**
     * Track order
     */
    async track(orderId) {
        return apiRequest(`/orders/${orderId}/track`);
    },
};

// ============================================================
// Admin API
// ============================================================
// Admin-only endpoints for dashboard management.
// All endpoints require admin authentication.

const AdminAPI = {
    // ----------------------------------------------------------
    // Dashboard Stats
    // ----------------------------------------------------------

    /**
     * Get dashboard statistics
     * Returns product counts, order counts, user counts, and revenue
     */
    async getStats() {
        return apiRequest('/admin/stats');
    },

    // ----------------------------------------------------------
    // Product Management
    // ----------------------------------------------------------

    /**
     * Get all products (including inactive)
     * @param {Object} params - Query parameters
     * @param {number} params.page - Page number (default 1)
     * @param {number} params.perPage - Items per page (default 20)
     * @param {string} params.search - Search term
     * @param {string} params.category - Category filter
     */
    async getProducts(params = {}) {
        const queryParams = new URLSearchParams();
        if (params.page) queryParams.set('page', params.page);
        if (params.perPage) queryParams.set('per_page', params.perPage);
        if (params.search) queryParams.set('search', params.search);
        if (params.category) queryParams.set('category', params.category);

        const query = queryParams.toString();
        return apiRequest(`/admin/products${query ? '?' + query : ''}`);
    },

    /**
     * Toggle product active status
     * @param {string} productId - Product ID
     */
    async toggleProductActive(productId) {
        return apiRequest(`/admin/products/${productId}/toggle-active`, {
            method: 'PUT',
        });
    },

    /**
     * Create new product
     * Uses the existing products endpoint (admin only)
     * @param {Object} productData - Product data
     */
    async createProduct(productData) {
        return apiRequest('/products', {
            method: 'POST',
            body: JSON.stringify(productData),
        });
    },

    /**
     * Update product
     * Uses the existing products endpoint (admin only)
     * @param {string} productId - Product ID
     * @param {Object} productData - Updated product data
     */
    async updateProduct(productId, productData) {
        return apiRequest(`/products/${productId}`, {
            method: 'PUT',
            body: JSON.stringify(productData),
        });
    },

    /**
     * Delete product (soft delete)
     * Uses the existing products endpoint (admin only)
     * @param {string} productId - Product ID
     */
    async deleteProduct(productId) {
        return apiRequest(`/products/${productId}`, {
            method: 'DELETE',
        });
    },

    // ----------------------------------------------------------
    // Order Management
    // ----------------------------------------------------------

    /**
     * Get all orders (admin view)
     * @param {Object} params - Query parameters
     * @param {number} params.page - Page number
     * @param {number} params.perPage - Items per page
     * @param {string} params.status - Status filter
     * @param {string} params.search - Search term (order # or email)
     */
    async getOrders(params = {}) {
        const queryParams = new URLSearchParams();
        if (params.page) queryParams.set('page', params.page);
        if (params.perPage) queryParams.set('per_page', params.perPage);
        if (params.status) queryParams.set('status', params.status);
        if (params.search) queryParams.set('search', params.search);

        const query = queryParams.toString();
        return apiRequest(`/admin/orders${query ? '?' + query : ''}`);
    },

    /**
     * Get order details (admin view with customer info)
     * @param {string} orderId - Order ID
     */
    async getOrder(orderId) {
        return apiRequest(`/admin/orders/${orderId}`);
    },

    /**
     * Update order status
     * @param {string} orderId - Order ID
     * @param {string} status - New status
     * @param {string} notes - Optional notes about the status change
     */
    async updateOrderStatus(orderId, status, notes = null) {
        return apiRequest(`/admin/orders/${orderId}/status`, {
            method: 'PUT',
            body: JSON.stringify({ status, notes }),
        });
    },

    // ----------------------------------------------------------
    // User Management
    // ----------------------------------------------------------

    /**
     * Get all users
     * @param {Object} params - Query parameters
     * @param {number} params.page - Page number
     * @param {number} params.perPage - Items per page
     * @param {string} params.status - Status filter (active, inactive, admin)
     * @param {string} params.search - Search term (name or email)
     */
    async getUsers(params = {}) {
        const queryParams = new URLSearchParams();
        if (params.page) queryParams.set('page', params.page);
        if (params.perPage) queryParams.set('per_page', params.perPage);
        if (params.status) queryParams.set('status', params.status);
        if (params.search) queryParams.set('search', params.search);

        const query = queryParams.toString();
        return apiRequest(`/admin/users${query ? '?' + query : ''}`);
    },

    /**
     * Get user details (admin view with order stats)
     * @param {string} userId - User ID
     */
    async getUser(userId) {
        return apiRequest(`/admin/users/${userId}`);
    },

    /**
     * Toggle user active status
     * @param {string} userId - User ID
     * @param {boolean} isActive - New active status
     */
    async toggleUserStatus(userId, isActive) {
        return apiRequest(`/admin/users/${userId}/status`, {
            method: 'PUT',
            body: JSON.stringify({ is_active: isActive }),
        });
    },
};

// Export for use in other scripts
window.API = {
    Auth: AuthAPI,
    Users: UsersAPI,
    Products: ProductsAPI,
    Cart: CartAPI,
    Addresses: AddressesAPI,
    Orders: OrdersAPI,
    Admin: AdminAPI,
    isAuthenticated,
    getCurrentUser,
    clearAuth,
};
