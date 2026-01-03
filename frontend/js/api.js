/**
 * E-Commerce API Client
 * Handles all API communication with the backend
 */

// API Base URL - uses nginx proxy in Docker
const API_BASE_URL = '/api';

// Store for auth token
let authToken = localStorage.getItem('authToken');
let currentUser = JSON.parse(localStorage.getItem('currentUser') || 'null');

// Simple cache for GET requests (5 minute TTL)
const apiCache = new Map();
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

function getCached(key) {
    const cached = apiCache.get(key);
    if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
        return cached.data;
    }
    apiCache.delete(key);
    return null;
}

function setCache(key, data) {
    apiCache.set(key, { data, timestamp: Date.now() });
}

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

// Export for use in other scripts
window.API = {
    Auth: AuthAPI,
    Users: UsersAPI,
    Products: ProductsAPI,
    Cart: CartAPI,
    Addresses: AddressesAPI,
    Orders: OrdersAPI,
    isAuthenticated,
    getCurrentUser,
    clearAuth,
};
