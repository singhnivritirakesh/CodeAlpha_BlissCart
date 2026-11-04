/**
 * Bliss Card - Admin & Seller Dashboards Logic
 * Real-time stats, order fulfillment, product creation, editing, and deletion.
 */

// Tab switching helper
function switchDashboardTab(tabId) {
  const tabs = document.querySelectorAll('.dashboard-tab');
  const panes = document.querySelectorAll('.tab-pane');

  tabs.forEach(t => t.classList.remove('active'));
  panes.forEach(p => p.classList.remove('active'));

  const activeTab = document.querySelector(`.dashboard-tab[data-tab="${tabId}"]`);
  const activePane = document.getElementById(tabId);

  if (activeTab) activeTab.classList.add('active');
  if (activePane) activePane.classList.add('active');
}

// Modal open/close helpers
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.classList.add('show');
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.classList.remove('show');
}

// ==============================================================================
// Admin Dashboard
// ==============================================================================

async function initAdminDashboard() {
  const root = document.getElementById('admin-dashboard-container');
  if (!root) return;

  try {
    const data = await apiRequest('/api/dashboard/admin/');
    const stats = data.stats;

    // Render Stats
    document.getElementById('stat-revenue').innerText = `$${stats.total_revenue.toFixed(2)}`;
    document.getElementById('stat-orders').innerText = stats.total_orders;
    document.getElementById('stat-pending').innerText = stats.pending_orders;
    document.getElementById('stat-users').innerText = stats.total_users;
    document.getElementById('stat-users-subtext').innerText = `${stats.total_sellers} sellers · ${stats.total_buyers} buyers`;

    // Render Orders Table
    const ordersTbody = document.getElementById('admin-orders-tbody');
    if (ordersTbody) {
      if (data.recent_orders.length === 0) {
        ordersTbody.innerHTML = `<tr><td colspan="6" style="text-align:center;padding:2rem;">No orders found.</td></tr>`;
      } else {
        ordersTbody.innerHTML = data.recent_orders.map(order => `
          <tr>
            <td><strong>#${order.id}</strong></td>
            <td>${order.buyer_username}</td>
            <td>$${parseFloat(order.total_amount).toFixed(2)}</td>
            <td>${formatDate(order.created_at)}</td>
            <td>
              <select 
                class="form-control" 
                style="padding:0.3rem 0.5rem;font-size:0.85rem;width:auto;"
                onchange="handleAdminOrderStatusChange(${order.id}, this.value)"
              >
                <option value="Pending" ${order.status === 'Pending' ? 'selected' : ''}>Pending</option>
                <option value="Shipped" ${order.status === 'Shipped' ? 'selected' : ''}>Shipped</option>
                <option value="Delivered" ${order.status === 'Delivered' ? 'selected' : ''}>Delivered</option>
                <option value="Cancelled" ${order.status === 'Cancelled' ? 'selected' : ''}>Cancelled</option>
              </select>
            </td>
            <td>
              <span class="badge ${getStatusBadge(order.status)}">${order.status}</span>
            </td>
          </tr>
        `).join('');
      }
    }

    // Render Products Table
    const productsTbody = document.getElementById('admin-products-tbody');
    if (productsTbody) {
      if (data.products.length === 0) {
        productsTbody.innerHTML = `<tr><td colspan="6" style="text-align:center;padding:2rem;">No products found.</td></tr>`;
      } else {
        productsTbody.innerHTML = data.products.map(p => `
          <tr>
            <td>
              <div style="display:flex;align-items:center;gap:0.75rem;">
                <img src="${p.image_display_url}" style="width:36px;height:36px;border-radius:4px;object-fit:cover;" />
                <a href="/products/${p.id}/" target="_blank" style="font-weight:600;color:var(--secondary);">${p.title}</a>
              </div>
            </td>
            <td>${p.seller?.username || 'Unknown'}</td>
            <td>${p.category?.name || 'None'}</td>
            <td><strong>$${parseFloat(p.price).toFixed(2)}</strong></td>
            <td>${p.stock} in stock</td>
            <td>
              <button class="btn btn-sm btn-outline" style="color:var(--danger);" onclick="handleAdminDeleteProduct(${p.id})">
                Delete
              </button>
            </td>
          </tr>
        `).join('');
      }
    }

    // Render Users Table
    const usersTbody = document.getElementById('admin-users-tbody');
    if (usersTbody) {
      usersTbody.innerHTML = data.users.map(u => `
        <tr>
          <td><strong>${u.username}</strong></td>
          <td>${u.email || '—'}</td>
          <td><span class="badge badge-${u.role}">${u.role.toUpperCase()}</span></td>
          <td>${u.phone_number || '—'}</td>
          <td>${formatDate(u.date_joined)}</td>
        </tr>
      `).join('');
    }

  } catch (err) {
    if (err.status === 401 || err.status === 403) {
      showToast('Admin credentials required.', 'error');
      setTimeout(() => { window.location.href = '/login/'; }, 1000);
    }
  }
}

// Admin update order status
async function handleAdminOrderStatusChange(orderId, newStatus) {
  try {
    await apiRequest(`/api/orders/${orderId}/status/`, 'PATCH', { status: newStatus });
    showToast(`Order #${orderId} status updated to ${newStatus}.`, 'success');
    initAdminDashboard();
  } catch (err) {
    showToast(err.data?.detail || err.message || 'Update failed.', 'error');
  }
}

// Admin delete product
async function handleAdminDeleteProduct(productId) {
  if (!confirm('Are you sure you want to permanently delete this product?')) return;
  try {
    await apiRequest(`/api/products/${productId}/`, 'DELETE');
    showToast('Product removed.', 'info');
    initAdminDashboard();
  } catch (err) {
    showToast(err.data?.detail || 'Delete failed.', 'error');
  }
}

// ==============================================================================
// Seller Dashboard
// ==============================================================================

async function initSellerDashboard() {
  const root = document.getElementById('seller-dashboard-container');
  if (!root) return;

  try {
    const data = await apiRequest('/api/dashboard/seller/');
    const stats = data.stats;

    // Render Stats
    document.getElementById('seller-stat-earnings').innerText = `$${stats.total_earnings.toFixed(2)}`;
    document.getElementById('seller-stat-units').innerText = stats.total_units_sold;
    document.getElementById('seller-stat-products').innerText = stats.total_products;
    document.getElementById('seller-stat-pending').innerText = stats.pending_fulfillments;

    // Render Seller Products Table
    const productsTbody = document.getElementById('seller-products-tbody');
    if (productsTbody) {
      if (data.products.length === 0) {
        productsTbody.innerHTML = `<tr><td colspan="6" style="text-align:center;padding:2rem;">You haven't published any cards yet. Click "+ Add New Card" to get started!</td></tr>`;
      } else {
        productsTbody.innerHTML = data.products.map(p => `
          <tr>
            <td>
              <div style="display:flex;align-items:center;gap:0.75rem;">
                <img src="${p.image_display_url}" style="width:40px;height:40px;border-radius:6px;object-fit:cover;" />
                <div>
                  <a href="/products/${p.id}/" target="_blank" style="font-weight:700;color:var(--secondary);">${p.title}</a>
                  <div style="font-size:0.75rem;color:var(--text-muted);">${p.category?.name || 'Uncategorized'}</div>
                </div>
              </div>
            </td>
            <td><strong>$${parseFloat(p.price).toFixed(2)}</strong></td>
            <td>
              ${p.stock > 0 
                ? `<span class="stock-tag in-stock">${p.stock} units</span>` 
                : `<span class="stock-tag out-of-stock">Sold out</span>`}
            </td>
            <td>${formatDate(p.created_at)}</td>
            <td>
              <div style="display:flex;gap:0.5rem;">
                <button class="btn btn-sm btn-outline" onclick='openEditProductModal(${JSON.stringify(p)})'>Edit</button>
                <button class="btn btn-sm btn-outline" style="color:var(--danger);" onclick="handleSellerDeleteProduct(${p.id})">Delete</button>
              </div>
            </td>
          </tr>
        `).join('');
      }
    }

    // Render Seller Orders Table
    const ordersTbody = document.getElementById('seller-orders-tbody');
    if (ordersTbody) {
      if (data.orders.length === 0) {
        ordersTbody.innerHTML = `<tr><td colspan="7" style="text-align:center;padding:2rem;">No orders received yet for your cards.</td></tr>`;
      } else {
        ordersTbody.innerHTML = data.orders.map(item => `
          <tr>
            <td><strong>#${item.order_id}</strong></td>
            <td>${formatDate(item.order_date)}</td>
            <td>
              <div style="font-weight:600;">${item.product_title}</div>
              <div style="font-size:0.8rem;color:var(--text-muted);">Buyer: ${item.buyer_username}</div>
            </td>
            <td>${item.quantity} × $${item.price.toFixed(2)}</td>
            <td><strong>$${item.subtotal.toFixed(2)}</strong></td>
            <td>
              <select 
                class="form-control" 
                style="padding:0.25rem 0.5rem;font-size:0.85rem;width:auto;"
                onchange="handleSellerOrderStatusChange(${item.order_id}, this.value)"
              >
                <option value="Pending" ${item.status === 'Pending' ? 'selected' : ''}>Pending</option>
                <option value="Shipped" ${item.status === 'Shipped' ? 'selected' : ''}>Shipped</option>
                <option value="Delivered" ${item.status === 'Delivered' ? 'selected' : ''}>Delivered</option>
              </select>
            </td>
            <td style="font-size:0.8rem;color:var(--text-secondary);max-width:200px;">
              ${item.shipping_address}
            </td>
          </tr>
        `).join('');
      }
    }

  } catch (err) {
    if (err.status === 401 || err.status === 403) {
      showToast('Seller account access required.', 'error');
      setTimeout(() => { window.location.href = '/login/'; }, 1000);
    }
  }
}

// Load Categories for the Add/Edit Product Modal dropdown
async function loadCategoryOptions(selectElementId, selectedId = null) {
  const select = document.getElementById(selectElementId);
  if (!select) return;

  try {
    const categories = await apiRequest('/api/categories/');
    select.innerHTML = '<option value="">-- Select a Category --</option>' + 
      categories.map(c => `
        <option value="${c.id}" ${selectedId === c.id ? 'selected' : ''}>${c.name}</option>
      `).join('');
  } catch (e) {
    console.warn('Could not load categories:', e);
  }
}

// Open Add Product Modal
function openAddProductModal() {
  const form = document.getElementById('add-product-form');
  if (form) form.reset();
  loadCategoryOptions('add-prod-category');
  openModal('add-product-modal');
}

// Open Edit Product Modal
function openEditProductModal(product) {
  document.getElementById('edit-prod-id').value = product.id;
  document.getElementById('edit-prod-title').value = product.title;
  document.getElementById('edit-prod-price').value = product.price;
  document.getElementById('edit-prod-stock').value = product.stock;
  document.getElementById('edit-prod-desc').value = product.description;
  document.getElementById('edit-prod-image-url').value = product.image_url || '';

  loadCategoryOptions('edit-prod-category', product.category?.id);
  openModal('edit-product-modal');
}

// Submit Add Product Form
async function handleAddProductSubmit(e) {
  e.preventDefault();
  const title = document.getElementById('add-prod-title').value.trim();
  const price = document.getElementById('add-prod-price').value;
  const stock = document.getElementById('add-prod-stock').value;
  const categoryId = document.getElementById('add-prod-category').value;
  const description = document.getElementById('add-prod-desc').value.trim();
  const imageUrl = document.getElementById('add-prod-image-url').value.trim();
  const submitBtn = document.getElementById('add-prod-submit-btn');

  if (!title || !price || !stock || !description) {
    showToast('Please fill all required fields.', 'warning');
    return;
  }

  submitBtn.disabled = true;
  submitBtn.innerText = 'Publishing...';

  const payload = {
    title,
    price: parseFloat(price).toFixed(2),
    stock: parseInt(stock),
    description,
    image_url: imageUrl || undefined,
  };
  if (categoryId) payload.category_id = parseInt(categoryId);

  try {
    await apiRequest('/api/products/', 'POST', payload);
    showToast('🎉 New card published successfully!', 'success');
    closeModal('add-product-modal');
    initSellerDashboard();
  } catch (err) {
    showToast(err.data?.detail || err.message || 'Failed to publish card.', 'error');
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerText = 'Publish Card';
  }
}

// Submit Edit Product Form
async function handleEditProductSubmit(e) {
  e.preventDefault();
  const id = document.getElementById('edit-prod-id').value;
  const title = document.getElementById('edit-prod-title').value.trim();
  const price = document.getElementById('edit-prod-price').value;
  const stock = document.getElementById('edit-prod-stock').value;
  const categoryId = document.getElementById('edit-prod-category').value;
  const description = document.getElementById('edit-prod-desc').value.trim();
  const imageUrl = document.getElementById('edit-prod-image-url').value.trim();
  const submitBtn = document.getElementById('edit-prod-submit-btn');

  submitBtn.disabled = true;
  submitBtn.innerText = 'Saving...';

  const payload = {
    title,
    price: parseFloat(price).toFixed(2),
    stock: parseInt(stock),
    description,
    image_url: imageUrl || undefined,
    category_id: categoryId ? parseInt(categoryId) : null,
  };

  try {
    await apiRequest(`/api/products/${id}/`, 'PUT', payload);
    showToast('Product updated successfully.', 'success');
    closeModal('edit-product-modal');
    initSellerDashboard();
  } catch (err) {
    showToast(err.data?.detail || err.message || 'Failed to update product.', 'error');
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerText = 'Save Changes';
  }
}

// Seller delete product
async function handleSellerDeleteProduct(productId) {
  if (!confirm('Are you sure you want to delete this greeting card?')) return;
  try {
    await apiRequest(`/api/products/${productId}/`, 'DELETE');
    showToast('Card deleted from inventory.', 'info');
    initSellerDashboard();
  } catch (err) {
    showToast(err.data?.detail || 'Delete failed.', 'error');
  }
}

// Seller update order status
async function handleSellerOrderStatusChange(orderId, newStatus) {
  try {
    await apiRequest(`/api/orders/${orderId}/status/`, 'PATCH', { status: newStatus });
    showToast(`Order #${orderId} marked as ${newStatus}.`, 'success');
    initSellerDashboard();
  } catch (err) {
    showToast(err.data?.detail || err.message || 'Status update failed.', 'error');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('admin-dashboard-container')) {
    initAdminDashboard();
  }

  if (document.getElementById('seller-dashboard-container')) {
    initSellerDashboard();

    const addForm = document.getElementById('add-product-form');
    if (addForm) addForm.addEventListener('submit', handleAddProductSubmit);

    const editForm = document.getElementById('edit-product-form');
    if (editForm) editForm.addEventListener('submit', handleEditProductSubmit);
  }
});

