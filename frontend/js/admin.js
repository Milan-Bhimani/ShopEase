/**
 * ==============================================================================
 * Admin Dashboard JavaScript (admin.js)
 * ==============================================================================
 *
 * PURPOSE:
 * --------
 * This module handles all client-side logic for the admin dashboard:
 * - Authentication check and admin verification
 * - Section navigation (hash-based routing)
 * - Dashboard statistics loading
 * - Product management (CRUD operations)
 * - Order management (view, update status)
 * - User management (view, toggle status)
 *
 * DEPENDENCIES:
 * -------------
 * - utils.js: Utility functions (formatPrice, formatDate, showToast)
 * - api.js: API client with AdminAPI object
 * - Bootstrap 5: Modal, Toast components
 *
 * SECTIONS:
 * ---------
 * 1. INITIALIZATION - Auth check, section routing
 * 2. DASHBOARD - Stats cards, status breakdown, recent orders
 * 3. PRODUCTS - Table, CRUD modals, toggle active
 * 4. ORDERS - Table, details modal, status update
 * 5. USERS - Table, details modal, toggle status
 * 6. UTILITIES - Helpers, pagination, toast notifications
 */

// ==============================================================================
// 1. INITIALIZATION
// ==============================================================================

/**
 * Current page states
 * Tracks pagination and filters for each section
 */
const pageState = {
    products: { page: 1, perPage: 20, search: '', category: '' },
    orders: { page: 1, perPage: 20, search: '', status: '' },
    users: { page: 1, perPage: 20, search: '', status: '' },
};

/**
 * Currently selected item for modals
 */
let currentOrderId = null;
let currentUserId = null;
let currentProductId = null;

/**
 * Bootstrap modal instances
 * Initialized after DOM loads
 */
let orderModal, userModal, productModal, updateStatusModal, confirmDeleteModal;

/**
 * Initialize admin dashboard on page load
 * Checks authentication and sets up routing
 */
document.addEventListener('DOMContentLoaded', async () => {
    // Check if user is authenticated
    if (!API.isAuthenticated()) {
        window.location.href = '/login.html?redirect=/admin.html';
        return;
    }

    // Verify user is admin
    try {
        const user = API.getCurrentUser();
        if (!user || !user.is_admin) {
            // Try fetching profile to verify
            const profile = await API.Auth.getProfile();
            if (!profile.is_admin) {
                showToast('Access Denied', 'Admin privileges required', 'danger');
                setTimeout(() => {
                    window.location.href = '/index.html';
                }, 1500);
                return;
            }
        }

        // Update admin name in sidebar
        if (user) {
            document.getElementById('adminName').textContent =
                `${user.first_name || ''} ${user.last_name || ''}`.trim() || user.email;
        }
    } catch (error) {
        console.error('Auth check failed:', error);
        window.location.href = '/login.html';
        return;
    }

    // Initialize Bootstrap modals
    orderModal = new bootstrap.Modal(document.getElementById('orderModal'));
    userModal = new bootstrap.Modal(document.getElementById('userModal'));
    productModal = new bootstrap.Modal(document.getElementById('productModal'));
    updateStatusModal = new bootstrap.Modal(document.getElementById('updateStatusModal'));
    confirmDeleteModal = new bootstrap.Modal(document.getElementById('confirmDeleteModal'));

    // Set up navigation
    setupNavigation();

    // Handle initial hash or default to dashboard
    const hash = window.location.hash.slice(1) || 'dashboard';
    navigateToSection(hash);

    // Set up search enter key handlers
    setupSearchHandlers();
});

/**
 * Set up sidebar navigation click handlers
 */
function setupNavigation() {
    const navItems = document.querySelectorAll('.admin-nav-item[data-section]');

    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            const section = item.dataset.section;
            navigateToSection(section);
        });
    });

    // Listen for hash changes
    window.addEventListener('hashchange', () => {
        const hash = window.location.hash.slice(1);
        if (hash) {
            navigateToSection(hash);
        }
    });
}

/**
 * Navigate to a section and load its data
 * @param {string} section - Section name (dashboard, products, orders, users)
 */
function navigateToSection(section) {
    // Update active nav item
    document.querySelectorAll('.admin-nav-item').forEach(item => {
        item.classList.remove('active');
        if (item.dataset.section === section) {
            item.classList.add('active');
        }
    });

    // Hide all sections
    document.querySelectorAll('.admin-section').forEach(sec => {
        sec.style.display = 'none';
    });

    // Show selected section
    const sectionElement = document.getElementById(`${section}Section`);
    if (sectionElement) {
        sectionElement.style.display = 'block';
    }

    // Update page title
    const titles = {
        dashboard: 'Dashboard',
        products: 'Products',
        orders: 'Orders',
        users: 'Users',
    };
    document.getElementById('pageTitle').textContent = titles[section] || 'Dashboard';

    // Load section data
    switch (section) {
        case 'dashboard':
            loadDashboard();
            break;
        case 'products':
            loadProducts();
            break;
        case 'orders':
            loadOrders();
            break;
        case 'users':
            loadUsers();
            break;
    }

    // Close mobile sidebar
    document.getElementById('adminSidebar').classList.remove('open');
}

/**
 * Set up search input enter key handlers
 */
function setupSearchHandlers() {
    // Product search
    document.getElementById('productSearch').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') searchProducts();
    });

    // Order search
    document.getElementById('orderSearch').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') searchOrders();
    });

    // User search
    document.getElementById('userSearch').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') searchUsers();
    });
}

/**
 * Toggle mobile sidebar
 */
function toggleSidebar() {
    document.getElementById('adminSidebar').classList.toggle('open');
}

/**
 * Logout and redirect to home
 */
async function logout() {
    try {
        await API.Auth.logout();
    } catch (e) {
        // Ignore logout errors
    }
    window.location.href = '/index.html';
}


// ==============================================================================
// 2. DASHBOARD - Stats and overview
// ==============================================================================

/**
 * Load dashboard statistics
 */
async function loadDashboard() {
    try {
        const stats = await API.Admin.getStats();
        renderStatsCards(stats);
        renderStatusBreakdown(stats.orders_by_status);
        await loadRecentOrders();
    } catch (error) {
        console.error('Failed to load dashboard:', error);
        showToast('Error', 'Failed to load dashboard statistics', 'danger');
    }
}

/**
 * Render stats cards grid
 * @param {Object} stats - Statistics object from API
 */
function renderStatsCards(stats) {
    const grid = document.getElementById('statsGrid');
    grid.innerHTML = `
        <!-- Products Card -->
        <div class="stat-card">
            <div class="stat-card-icon products">
                <i class="bi bi-box-seam"></i>
            </div>
            <div class="stat-card-content">
                <h3>${stats.total_products}</h3>
                <p>Total Products (${stats.active_products} active)</p>
            </div>
        </div>

        <!-- Orders Card -->
        <div class="stat-card">
            <div class="stat-card-icon orders">
                <i class="bi bi-receipt"></i>
            </div>
            <div class="stat-card-content">
                <h3>${stats.total_orders}</h3>
                <p>Total Orders (${stats.recent_orders} this week)</p>
            </div>
        </div>

        <!-- Users Card -->
        <div class="stat-card">
            <div class="stat-card-icon users">
                <i class="bi bi-people"></i>
            </div>
            <div class="stat-card-content">
                <h3>${stats.total_users}</h3>
                <p>Total Users (${stats.active_users} active)</p>
            </div>
        </div>

        <!-- Revenue Card -->
        <div class="stat-card">
            <div class="stat-card-icon revenue">
                <i class="bi bi-currency-rupee"></i>
            </div>
            <div class="stat-card-content">
                <h3>${formatPrice(stats.total_revenue)}</h3>
                <p>Total Revenue</p>
            </div>
        </div>
    `;
}

/**
 * Render order status breakdown
 * @param {Object} statusCounts - Object mapping status to count
 */
function renderStatusBreakdown(statusCounts) {
    const container = document.getElementById('statusBreakdown');

    // Status display configuration
    const statusConfig = {
        pending: { color: '#ffc107', label: 'Pending' },
        confirmed: { color: '#17a2b8', label: 'Confirmed' },
        processing: { color: '#007bff', label: 'Processing' },
        shipped: { color: '#6f42c1', label: 'Shipped' },
        out_for_delivery: { color: '#20c997', label: 'Out for Delivery' },
        delivered: { color: '#28a745', label: 'Delivered' },
        cancelled: { color: '#dc3545', label: 'Cancelled' },
        returned: { color: '#fd7e14', label: 'Returned' },
    };

    let html = '<h5>Orders by Status</h5>';

    for (const [status, config] of Object.entries(statusConfig)) {
        const count = statusCounts[status] || 0;
        html += `
            <div class="status-item">
                <div class="label">
                    <span class="dot" style="background: ${config.color}"></span>
                    <span>${config.label}</span>
                </div>
                <span class="count">${count}</span>
            </div>
        `;
    }

    container.innerHTML = html;
}

/**
 * Load recent orders for dashboard
 */
async function loadRecentOrders() {
    try {
        const response = await API.Admin.getOrders({ page: 1, perPage: 5 });
        const tbody = document.querySelector('#recentOrdersTable tbody');

        if (response.orders.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" class="text-center py-4 text-muted">
                        No orders yet
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = response.orders.map(order => `
            <tr>
                <td><strong>${order.order_number || order.id}</strong></td>
                <td>${order.user ? `${order.user.first_name} ${order.user.last_name}` : 'Guest'}</td>
                <td>${formatPrice(order.total)}</td>
                <td><span class="status-badge ${order.status}">${formatStatus(order.status)}</span></td>
                <td>${formatDate(order.created_at)}</td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Failed to load recent orders:', error);
    }
}


// ==============================================================================
// 3. PRODUCTS - Product management
// ==============================================================================

/**
 * Load products table
 */
async function loadProducts() {
    const tbody = document.querySelector('#productsTable tbody');
    tbody.innerHTML = '<tr><td colspan="7" class="text-center py-4"><div class="spinner-border text-primary" role="status"></div></td></tr>';

    try {
        const response = await API.Admin.getProducts(pageState.products);

        if (response.products.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center py-4 text-muted">
                        No products found
                    </td>
                </tr>
            `;
            renderPagination('products', response);
            return;
        }

        tbody.innerHTML = response.products.map(product => `
            <tr>
                <td>
                    <img src="${product.thumbnail || product.images?.[0] || 'https://via.placeholder.com/50'}"
                         alt="${product.name}" class="product-thumb">
                </td>
                <td>
                    <strong>${product.name}</strong>
                    <br><small class="text-muted">${product.sku || ''}</small>
                </td>
                <td>${product.category || '-'}</td>
                <td>
                    ${formatPrice(product.price)}
                    ${product.original_price > product.price ?
                        `<br><small class="text-muted text-decoration-line-through">${formatPrice(product.original_price)}</small>` : ''}
                </td>
                <td>${product.stock_quantity || product.stock || 0}</td>
                <td>
                    <span class="status-badge ${product.is_active ? 'active' : 'inactive'}">
                        ${product.is_active ? 'Active' : 'Inactive'}
                    </span>
                </td>
                <td>
                    <button class="action-btn edit" onclick="editProduct('${product.id}')" title="Edit">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="action-btn toggle" onclick="toggleProductStatus('${product.id}')" title="Toggle Active">
                        <i class="bi bi-toggle-on"></i>
                    </button>
                    <button class="action-btn delete" onclick="confirmDeleteProduct('${product.id}')" title="Delete">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            </tr>
        `).join('');

        renderPagination('products', response);
    } catch (error) {
        console.error('Failed to load products:', error);
        tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-danger">Failed to load products</td></tr>`;
    }
}

/**
 * Search products
 */
function searchProducts() {
    pageState.products.search = document.getElementById('productSearch').value;
    pageState.products.page = 1;
    loadProducts();
}

/**
 * Filter products by category
 */
function filterProducts() {
    pageState.products.category = document.getElementById('productCategoryFilter').value;
    pageState.products.page = 1;
    loadProducts();
}

/**
 * Show add product modal
 */
function showAddProductModal() {
    currentProductId = null;
    document.getElementById('productModalTitle').textContent = 'Add Product';
    document.getElementById('productForm').reset();
    document.getElementById('productActive').checked = true;
    productModal.show();
}

/**
 * Edit existing product
 * @param {string} productId - Product ID
 */
async function editProduct(productId) {
    try {
        const product = await API.Products.getProduct(productId);
        currentProductId = productId;

        document.getElementById('productModalTitle').textContent = 'Edit Product';
        document.getElementById('productId').value = productId;
        document.getElementById('productName').value = product.name || '';
        document.getElementById('productDescription').value = product.description || '';
        document.getElementById('productCategory').value = product.category || '';
        document.getElementById('productBrand').value = product.brand || '';
        document.getElementById('productSku').value = product.sku || '';
        document.getElementById('productPrice').value = product.price || '';
        document.getElementById('productOriginalPrice').value = product.original_price || '';
        document.getElementById('productStock').value = product.stock_quantity || product.stock || 0;
        document.getElementById('productImages').value = (product.images || []).join(', ');
        document.getElementById('productFeatured').checked = product.is_featured || false;
        document.getElementById('productActive').checked = product.is_active !== false;

        productModal.show();
    } catch (error) {
        console.error('Failed to load product:', error);
        showToast('Error', 'Failed to load product details', 'danger');
    }
}

/**
 * Save product (create or update)
 */
async function saveProduct() {
    const form = document.getElementById('productForm');
    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }

    const productData = {
        name: document.getElementById('productName').value,
        description: document.getElementById('productDescription').value,
        category: document.getElementById('productCategory').value,
        brand: document.getElementById('productBrand').value,
        sku: document.getElementById('productSku').value,
        price: parseFloat(document.getElementById('productPrice').value),
        original_price: parseFloat(document.getElementById('productOriginalPrice').value) || null,
        stock_quantity: parseInt(document.getElementById('productStock').value),
        images: document.getElementById('productImages').value.split(',').map(s => s.trim()).filter(Boolean),
        is_featured: document.getElementById('productFeatured').checked,
        is_active: document.getElementById('productActive').checked,
    };

    // Set thumbnail from first image
    if (productData.images.length > 0) {
        productData.thumbnail = productData.images[0];
    }

    // Create name_lower for search
    productData.name_lower = productData.name.toLowerCase();

    try {
        if (currentProductId) {
            await API.Admin.updateProduct(currentProductId, productData);
            showToast('Success', 'Product updated successfully', 'success');
        } else {
            await API.Admin.createProduct(productData);
            showToast('Success', 'Product created successfully', 'success');
        }
        productModal.hide();
        loadProducts();
    } catch (error) {
        console.error('Failed to save product:', error);
        showToast('Error', error.message || 'Failed to save product', 'danger');
    }
}

/**
 * Toggle product active status
 * @param {string} productId - Product ID
 */
async function toggleProductStatus(productId) {
    try {
        const result = await API.Admin.toggleProductActive(productId);
        showToast('Success', result.message, 'success');
        loadProducts();
    } catch (error) {
        console.error('Failed to toggle product status:', error);
        showToast('Error', 'Failed to update product status', 'danger');
    }
}

/**
 * Show delete confirmation modal
 * @param {string} productId - Product ID
 */
function confirmDeleteProduct(productId) {
    currentProductId = productId;
    document.getElementById('deleteConfirmText').textContent =
        'Are you sure you want to delete this product? This action cannot be undone.';
    document.getElementById('confirmDeleteBtn').onclick = deleteProduct;
    confirmDeleteModal.show();
}

/**
 * Delete product
 */
async function deleteProduct() {
    try {
        await API.Admin.deleteProduct(currentProductId);
        confirmDeleteModal.hide();
        showToast('Success', 'Product deleted successfully', 'success');
        loadProducts();
    } catch (error) {
        console.error('Failed to delete product:', error);
        showToast('Error', error.message || 'Failed to delete product', 'danger');
    }
}


// ==============================================================================
// 4. ORDERS - Order management
// ==============================================================================

/**
 * Load orders table
 */
async function loadOrders() {
    const tbody = document.querySelector('#ordersTable tbody');
    tbody.innerHTML = '<tr><td colspan="8" class="text-center py-4"><div class="spinner-border text-primary" role="status"></div></td></tr>';

    try {
        const response = await API.Admin.getOrders(pageState.orders);

        if (response.orders.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="text-center py-4 text-muted">
                        No orders found
                    </td>
                </tr>
            `;
            renderPagination('orders', response);
            return;
        }

        tbody.innerHTML = response.orders.map(order => `
            <tr>
                <td><strong>${order.order_number || order.id}</strong></td>
                <td>
                    ${order.user ? `${order.user.first_name} ${order.user.last_name}` : 'Guest'}
                    ${order.user ? `<br><small class="text-muted">${order.user.email}</small>` : ''}
                </td>
                <td>${order.items ? order.items.length : 0} items</td>
                <td>${formatPrice(order.total)}</td>
                <td>
                    <span class="badge bg-${order.payment_status === 'paid' ? 'success' : 'warning'}">
                        ${order.payment_method || 'N/A'}
                    </span>
                </td>
                <td><span class="status-badge ${order.status}">${formatStatus(order.status)}</span></td>
                <td>${formatDate(order.created_at)}</td>
                <td>
                    <button class="action-btn view" onclick="viewOrder('${order.id}')" title="View Details">
                        <i class="bi bi-eye"></i>
                    </button>
                    <button class="action-btn edit" onclick="showUpdateStatusModal('${order.id}', '${order.status}')" title="Update Status">
                        <i class="bi bi-pencil"></i>
                    </button>
                </td>
            </tr>
        `).join('');

        renderPagination('orders', response);
    } catch (error) {
        console.error('Failed to load orders:', error);
        tbody.innerHTML = `<tr><td colspan="8" class="text-center py-4 text-danger">Failed to load orders</td></tr>`;
    }
}

/**
 * Search orders
 */
function searchOrders() {
    pageState.orders.search = document.getElementById('orderSearch').value;
    pageState.orders.page = 1;
    loadOrders();
}

/**
 * Filter orders by status
 */
function filterOrders() {
    pageState.orders.status = document.getElementById('orderStatusFilter').value;
    pageState.orders.page = 1;
    loadOrders();
}

/**
 * View order details in modal
 * @param {string} orderId - Order ID
 */
async function viewOrder(orderId) {
    currentOrderId = orderId;

    try {
        const order = await API.Admin.getOrder(orderId);
        const modalBody = document.getElementById('orderModalBody');

        modalBody.innerHTML = `
            <!-- Order Header -->
            <div class="order-detail-section">
                <div class="row">
                    <div class="col-md-6">
                        <h6>Order Information</h6>
                        <p class="mb-1"><strong>Order #:</strong> ${order.order_number || order.id}</p>
                        <p class="mb-1"><strong>Date:</strong> ${formatDate(order.created_at)}</p>
                        <p class="mb-1"><strong>Status:</strong> <span class="status-badge ${order.status}">${formatStatus(order.status)}</span></p>
                    </div>
                    <div class="col-md-6">
                        <h6>Customer Information</h6>
                        ${order.user ? `
                            <p class="mb-1"><strong>Name:</strong> ${order.user.first_name} ${order.user.last_name}</p>
                            <p class="mb-1"><strong>Email:</strong> ${order.user.email}</p>
                            <p class="mb-1"><strong>Phone:</strong> ${order.user.phone || 'N/A'}</p>
                        ` : '<p class="text-muted">Guest order</p>'}
                    </div>
                </div>
            </div>

            <!-- Shipping Address -->
            ${order.shipping_address ? `
                <div class="order-detail-section">
                    <h6>Shipping Address</h6>
                    <p class="mb-0">
                        ${order.shipping_address.full_name || ''}<br>
                        ${order.shipping_address.address_line1 || ''}<br>
                        ${order.shipping_address.address_line2 ? order.shipping_address.address_line2 + '<br>' : ''}
                        ${order.shipping_address.city || ''}, ${order.shipping_address.state || ''} ${order.shipping_address.pincode || ''}<br>
                        Phone: ${order.shipping_address.phone || 'N/A'}
                    </p>
                </div>
            ` : ''}

            <!-- Order Items -->
            <div class="order-detail-section">
                <h6>Order Items</h6>
                ${order.items.map(item => `
                    <div class="order-item-row">
                        <img src="${item.product_image || 'https://via.placeholder.com/60'}" alt="${item.product_name}">
                        <div class="order-item-details">
                            <div class="name">${item.product_name}</div>
                            <div class="meta">Qty: ${item.quantity} x ${formatPrice(item.price)}</div>
                        </div>
                        <div class="order-item-subtotal">
                            <strong>${formatPrice(item.subtotal || item.price * item.quantity)}</strong>
                        </div>
                    </div>
                `).join('')}
            </div>

            <!-- Order Summary -->
            <div class="order-detail-section">
                <h6>Order Summary</h6>
                <div class="d-flex justify-content-between mb-2">
                    <span>Subtotal:</span>
                    <span>${formatPrice(order.subtotal || order.total)}</span>
                </div>
                ${order.shipping_cost ? `
                    <div class="d-flex justify-content-between mb-2">
                        <span>Shipping:</span>
                        <span>${formatPrice(order.shipping_cost)}</span>
                    </div>
                ` : ''}
                ${order.discount ? `
                    <div class="d-flex justify-content-between mb-2 text-success">
                        <span>Discount:</span>
                        <span>-${formatPrice(order.discount)}</span>
                    </div>
                ` : ''}
                <div class="d-flex justify-content-between pt-2 border-top">
                    <strong>Total:</strong>
                    <strong>${formatPrice(order.total)}</strong>
                </div>
            </div>

            <!-- Payment Info -->
            <div class="order-detail-section">
                <h6>Payment Information</h6>
                <p class="mb-1"><strong>Method:</strong> ${order.payment_method || 'N/A'}</p>
                <p class="mb-1"><strong>Status:</strong> ${order.payment_status || 'N/A'}</p>
            </div>

            <!-- Notes -->
            ${order.notes ? `
                <div class="order-detail-section">
                    <h6>Notes</h6>
                    <p class="mb-0" style="white-space: pre-line;">${order.notes}</p>
                </div>
            ` : ''}
        `;

        orderModal.show();
    } catch (error) {
        console.error('Failed to load order details:', error);
        showToast('Error', 'Failed to load order details', 'danger');
    }
}

/**
 * Show update status modal from order modal
 */
function showUpdateStatusForm() {
    showUpdateStatusModal(currentOrderId);
    orderModal.hide();
}

/**
 * Show update status modal
 * @param {string} orderId - Order ID
 * @param {string} currentStatus - Current order status
 */
function showUpdateStatusModal(orderId, currentStatus = 'pending') {
    currentOrderId = orderId;
    document.getElementById('updateOrderId').value = orderId;
    document.getElementById('newOrderStatus').value = currentStatus;
    document.getElementById('statusNotes').value = '';
    updateStatusModal.show();
}

/**
 * Confirm and submit status update
 */
async function confirmUpdateStatus() {
    const orderId = document.getElementById('updateOrderId').value;
    const newStatus = document.getElementById('newOrderStatus').value;
    const notes = document.getElementById('statusNotes').value || null;

    try {
        await API.Admin.updateOrderStatus(orderId, newStatus, notes);
        updateStatusModal.hide();
        showToast('Success', 'Order status updated successfully', 'success');
        loadOrders();

        // Reload dashboard if visible
        if (document.getElementById('dashboardSection').style.display !== 'none') {
            loadDashboard();
        }
    } catch (error) {
        console.error('Failed to update order status:', error);
        showToast('Error', error.message || 'Failed to update order status', 'danger');
    }
}


// ==============================================================================
// 5. USERS - User management
// ==============================================================================

/**
 * Load users table
 */
async function loadUsers() {
    const tbody = document.querySelector('#usersTable tbody');
    tbody.innerHTML = '<tr><td colspan="8" class="text-center py-4"><div class="spinner-border text-primary" role="status"></div></td></tr>';

    try {
        const response = await API.Admin.getUsers(pageState.users);

        if (response.users.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="text-center py-4 text-muted">
                        No users found
                    </td>
                </tr>
            `;
            renderPagination('users', response);
            return;
        }

        tbody.innerHTML = response.users.map(user => `
            <tr>
                <td>
                    <strong>${user.first_name || ''} ${user.last_name || ''}</strong>
                    ${user.is_admin ? '<span class="status-badge admin-badge-role ms-1">Admin</span>' : ''}
                </td>
                <td>${user.email}</td>
                <td>${user.phone || '-'}</td>
                <td>${user.order_count || 0}</td>
                <td>${formatPrice(user.total_spent || 0)}</td>
                <td>
                    <span class="status-badge ${user.is_active ? 'active' : 'inactive'}">
                        ${user.is_active ? 'Active' : 'Inactive'}
                    </span>
                </td>
                <td>${formatDate(user.created_at)}</td>
                <td>
                    <button class="action-btn view" onclick="viewUser('${user.id}')" title="View Details">
                        <i class="bi bi-eye"></i>
                    </button>
                    ${!user.is_admin ? `
                        <button class="action-btn toggle" onclick="toggleUserStatus('${user.id}', ${!user.is_active})" title="Toggle Status">
                            <i class="bi bi-${user.is_active ? 'person-x' : 'person-check'}"></i>
                        </button>
                    ` : ''}
                </td>
            </tr>
        `).join('');

        renderPagination('users', response);
    } catch (error) {
        console.error('Failed to load users:', error);
        tbody.innerHTML = `<tr><td colspan="8" class="text-center py-4 text-danger">Failed to load users</td></tr>`;
    }
}

/**
 * Search users
 */
function searchUsers() {
    pageState.users.search = document.getElementById('userSearch').value;
    pageState.users.page = 1;
    loadUsers();
}

/**
 * Filter users by status
 */
function filterUsers() {
    pageState.users.status = document.getElementById('userStatusFilter').value;
    pageState.users.page = 1;
    loadUsers();
}

/**
 * View user details in modal
 * @param {string} userId - User ID
 */
async function viewUser(userId) {
    currentUserId = userId;

    try {
        const user = await API.Admin.getUser(userId);
        const modalBody = document.getElementById('userModalBody');

        modalBody.innerHTML = `
            <div class="text-center mb-4">
                <div class="admin-user-avatar mx-auto mb-3" style="width: 80px; height: 80px; font-size: 2rem; background: #e9ecef; color: #495057;">
                    <i class="bi bi-person-fill"></i>
                </div>
                <h5 class="mb-1">${user.first_name || ''} ${user.last_name || ''}</h5>
                <p class="text-muted mb-0">${user.email}</p>
                ${user.is_admin ? '<span class="status-badge admin-badge-role">Administrator</span>' : ''}
            </div>

            <div class="row text-center mb-4">
                <div class="col-6">
                    <h4 class="mb-0">${user.order_count || 0}</h4>
                    <small class="text-muted">Orders</small>
                </div>
                <div class="col-6">
                    <h4 class="mb-0">${formatPrice(user.total_spent || 0)}</h4>
                    <small class="text-muted">Total Spent</small>
                </div>
            </div>

            <table class="table table-sm">
                <tr>
                    <th>Phone:</th>
                    <td>${user.phone || 'Not provided'}</td>
                </tr>
                <tr>
                    <th>Status:</th>
                    <td>
                        <span class="status-badge ${user.is_active ? 'active' : 'inactive'}">
                            ${user.is_active ? 'Active' : 'Inactive'}
                        </span>
                    </td>
                </tr>
                <tr>
                    <th>Joined:</th>
                    <td>${formatDate(user.created_at)}</td>
                </tr>
                ${user.last_login ? `
                    <tr>
                        <th>Last Login:</th>
                        <td>${formatDate(user.last_login)}</td>
                    </tr>
                ` : ''}
            </table>

            ${!user.is_admin ? `
                <div class="text-center mt-4">
                    <button class="btn btn-${user.is_active ? 'danger' : 'success'}"
                            onclick="toggleUserStatus('${user.id}', ${!user.is_active}); userModal.hide();">
                        <i class="bi bi-${user.is_active ? 'person-x' : 'person-check'} me-1"></i>
                        ${user.is_active ? 'Deactivate User' : 'Activate User'}
                    </button>
                </div>
            ` : ''}
        `;

        userModal.show();
    } catch (error) {
        console.error('Failed to load user details:', error);
        showToast('Error', 'Failed to load user details', 'danger');
    }
}

/**
 * Toggle user active status
 * @param {string} userId - User ID
 * @param {boolean} newStatus - New active status
 */
async function toggleUserStatus(userId, newStatus) {
    try {
        await API.Admin.toggleUserStatus(userId, newStatus);
        showToast('Success', `User ${newStatus ? 'activated' : 'deactivated'} successfully`, 'success');
        loadUsers();

        // Update dashboard if visible
        if (document.getElementById('dashboardSection').style.display !== 'none') {
            loadDashboard();
        }
    } catch (error) {
        console.error('Failed to toggle user status:', error);
        showToast('Error', error.message || 'Failed to update user status', 'danger');
    }
}


// ==============================================================================
// 6. UTILITIES - Helpers and common functions
// ==============================================================================

/**
 * Format order status for display
 * @param {string} status - Raw status string
 * @returns {string} - Formatted status
 */
function formatStatus(status) {
    const statusMap = {
        pending: 'Pending',
        confirmed: 'Confirmed',
        processing: 'Processing',
        shipped: 'Shipped',
        out_for_delivery: 'Out for Delivery',
        delivered: 'Delivered',
        cancelled: 'Cancelled',
        returned: 'Returned',
    };
    return statusMap[status] || status;
}

/**
 * Format price in INR
 * @param {number} amount - Amount to format
 * @returns {string} - Formatted price string
 */
function formatPrice(amount) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        maximumFractionDigits: 0,
    }).format(amount || 0);
}

/**
 * Format date for display
 * @param {string} dateStr - ISO date string
 * @returns {string} - Formatted date
 */
function formatDate(dateStr) {
    if (!dateStr) return 'N/A';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-IN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
    });
}

/**
 * Render pagination controls
 * @param {string} section - Section name (products, orders, users)
 * @param {Object} response - API response with pagination info
 */
function renderPagination(section, response) {
    const container = document.getElementById(`${section}Pagination`);
    const state = pageState[section];
    const totalPages = Math.ceil(response.total / state.perPage);

    // Update page info
    const start = (state.page - 1) * state.perPage + 1;
    const end = Math.min(state.page * state.perPage, response.total);
    container.querySelector('.page-info').textContent =
        response.total > 0 ? `Showing ${start}-${end} of ${response.total}` : 'No results';

    // Generate pagination buttons
    const paginationList = container.querySelector('.pagination');
    let html = '';

    // Previous button
    html += `
        <li class="page-item ${state.page <= 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="goToPage('${section}', ${state.page - 1}); return false;">
                <i class="bi bi-chevron-left"></i>
            </a>
        </li>
    `;

    // Page numbers (show max 5 pages)
    const startPage = Math.max(1, state.page - 2);
    const endPage = Math.min(totalPages, startPage + 4);

    for (let i = startPage; i <= endPage; i++) {
        html += `
            <li class="page-item ${i === state.page ? 'active' : ''}">
                <a class="page-link" href="#" onclick="goToPage('${section}', ${i}); return false;">${i}</a>
            </li>
        `;
    }

    // Next button
    html += `
        <li class="page-item ${state.page >= totalPages ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="goToPage('${section}', ${state.page + 1}); return false;">
                <i class="bi bi-chevron-right"></i>
            </a>
        </li>
    `;

    paginationList.innerHTML = html;
}

/**
 * Navigate to a specific page
 * @param {string} section - Section name
 * @param {number} page - Page number
 */
function goToPage(section, page) {
    if (page < 1) return;
    pageState[section].page = page;

    switch (section) {
        case 'products':
            loadProducts();
            break;
        case 'orders':
            loadOrders();
            break;
        case 'users':
            loadUsers();
            break;
    }
}

/**
 * Show toast notification
 * @param {string} title - Toast title
 * @param {string} message - Toast message
 * @param {string} type - Bootstrap color (success, danger, warning, info)
 */
function showToast(title, message, type = 'info') {
    const toastEl = document.getElementById('adminToast');
    document.getElementById('toastTitle').textContent = title;
    document.getElementById('toastMessage').textContent = message;

    // Set toast header color based on type
    const header = toastEl.querySelector('.toast-header');
    header.className = `toast-header bg-${type} text-white`;

    const toast = new bootstrap.Toast(toastEl);
    toast.show();
}
