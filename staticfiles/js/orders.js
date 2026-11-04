/**
 * Bliss Card - Checkout & Order Processing Logic
 */

// Format date helper
function formatDate(isoString) {
  const d = new Date(isoString);
  return d.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

// Map status to badge CSS class
function getStatusBadge(status) {
  const lower = (status || '').toLowerCase();
  if (lower === 'delivered') return 'badge-delivered';
  if (lower === 'shipped') return 'badge-shipped';
  if (lower === 'cancelled') return 'badge-cancelled';
  return 'badge-pending';
}

// Initialize Checkout Page
async function initCheckoutPage() {
  const form = document.getElementById('checkout-form');
  const previewContainer = document.getElementById('checkout-items-preview');
  const totalDisplay = document.getElementById('checkout-total-amount');

  if (!form || !previewContainer) return;

  try {
    // 1. Load user profile for prefilling
    const userResp = await apiRequest('/api/auth/me/');
    if (!userResp.authenticated) {
      window.location.href = '/login/?next=/checkout/';
      return;
    }

    const user = userResp.user;
    if (user) {
      const nameField = document.getElementById('checkout-name');
      const phoneField = document.getElementById('checkout-phone');
      const addressField = document.getElementById('checkout-address');

      if (nameField && !nameField.value) {
        nameField.value = `${user.first_name || ''} ${user.last_name || ''}`.trim() || user.username;
      }
      if (phoneField && !phoneField.value && user.phone_number) {
        phoneField.value = user.phone_number;
      }
      if (addressField && !addressField.value && user.address) {
        addressField.value = user.address;
      }
    }

    // 2. Load Cart Items
    const cart = await apiRequest('/api/cart/');
    if (!cart.items || cart.items.length === 0) {
      showToast('Your cart is empty. Please add items before checking out.', 'warning');
      setTimeout(() => { window.location.href = '/cart/'; }, 1000);
      return;
    }

    // Render Preview
    previewContainer.innerHTML = cart.items.map(item => `
      <div class="checkout-item-mini">
        <img 
          src="${item.product.image_display_url}" 
          alt="${item.product.title}" 
          onerror="this.src='https://images.unsplash.com/photo-1513519245088-0e12902e5a38?w=200&auto=format&fit=crop&q=60'"
        />
        <div class="checkout-item-mini-info">
          <div class="checkout-item-mini-title">${item.product.title}</div>
          <div class="checkout-item-mini-qty">Qty: ${item.quantity} × $${parseFloat(item.product.price).toFixed(2)}</div>
        </div>
        <div style="font-weight: 700; color: var(--secondary);">
          $${parseFloat(item.subtotal).toFixed(2)}
        </div>
      </div>
    `).join('');

    if (totalDisplay) {
      totalDisplay.innerText = `$${parseFloat(cart.total_price).toFixed(2)}`;
    }

    // 3. Form Submit Listener
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      clearFormErrors('checkout-form');

      const fullName = document.getElementById('checkout-name').value.trim();
      const address = document.getElementById('checkout-address').value.trim();
      const city = document.getElementById('checkout-city').value.trim();
      const postalCode = document.getElementById('checkout-postal').value.trim();
      const phone = document.getElementById('checkout-phone').value.trim();
      const submitBtn = document.getElementById('place-order-btn');

      // Validation
      let hasError = false;
      if (!fullName) {
        setFieldError(document.getElementById('checkout-name'), 'Full name is required.');
        hasError = true;
      }
      if (!address) {
        setFieldError(document.getElementById('checkout-address'), 'Street address is required.');
        hasError = true;
      }
      if (!city) {
        setFieldError(document.getElementById('checkout-city'), 'City is required.');
        hasError = true;
      }
      if (!postalCode) {
        setFieldError(document.getElementById('checkout-postal'), 'Postal code is required.');
        hasError = true;
      }
      if (!phone) {
        setFieldError(document.getElementById('checkout-phone'), 'Phone number is required.');
        hasError = true;
      }
      if (hasError) return;

      submitBtn.disabled = true;
      submitBtn.innerText = 'Processing Order...';

      const payload = {
        full_name: fullName,
        shipping_address: address,
        city: city,
        postal_code: postalCode,
        phone: phone
      };

      try {
        const order = await apiRequest('/api/orders/checkout/', 'POST', payload);
        showToast('🎉 Order placed successfully! Thank you.', 'success', 5000);

        // Reset cart counter
        if (typeof refreshCartCount === 'function') {
          refreshCartCount();
        }

        setTimeout(() => {
          window.location.href = `/orders/?new=${order.id}`;
        }, 1000);

      } catch (err) {
        submitBtn.disabled = false;
        submitBtn.innerText = 'Complete Order & Pay';

        if (err.data && typeof err.data === 'object') {
          for (const [field, messages] of Object.entries(err.data)) {
            const input = document.getElementById(`checkout-${field}`);
            if (input) {
              setFieldError(input, Array.isArray(messages) ? messages[0] : messages);
            } else {
              showToast(Array.isArray(messages) ? messages[0] : messages, 'error');
            }
          }
        } else {
          showToast(err.message || 'Checkout failed. Please review your details.', 'error');
        }
      }
    });

  } catch (err) {
    console.error('Checkout initialization failed:', err);
  }
}

// Initialize Orders History Page
async function initOrdersPage() {
  const container = document.getElementById('orders-page-container');
  if (!container) return;

  container.innerHTML = `
    <div style="text-align: center; padding: 4rem 0; color: var(--text-secondary);">
      <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">✦ Loading your order history...</div>
    </div>
  `;

  try {
    const orders = await apiRequest('/api/orders/');

    if (orders.length === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-icon">📦</div>
          <h3>No Orders Yet</h3>
          <p>You haven't placed any orders yet. Discover our curated greeting cards and send something special.</p>
          <a href="/" class="btn btn-primary btn-lg">Start Shopping</a>
        </div>
      `;
      return;
    }

    container.innerHTML = `
      <div style="margin-bottom: 1.5rem;">
        <h1 style="font-size: 1.75rem; font-weight: 800; color: var(--secondary);">
          Your Orders (${orders.length})
        </h1>
        <p style="color: var(--text-secondary); font-size: 0.95rem;">Track order status, delivery, and receipt details.</p>
      </div>

      <div class="orders-list">
        ${orders.map(order => `
          <div class="order-card" id="order-${order.id}">
            <div class="order-card-header">
              <div class="order-meta-group">
                <div class="order-meta-item">
                  <span>Order Placed</span>
                  <strong>${formatDate(order.created_at)}</strong>
                </div>
                <div class="order-meta-item">
                  <span>Order ID</span>
                  <strong>#${order.id}</strong>
                </div>
                <div class="order-meta-item">
                  <span>Total Amount</span>
                  <strong>$${parseFloat(order.total_amount).toFixed(2)}</strong>
                </div>
              </div>

              <div style="display: flex; align-items: center; gap: 0.75rem;">
                <span class="badge ${getStatusBadge(order.status)}">${order.status}</span>
                ${order.status === 'Pending' ? `
                  <button class="btn btn-sm btn-outline" style="color:var(--danger); border-color:var(--border);" onclick="cancelCustomerOrder(${order.id})">
                    Cancel Order
                  </button>
                ` : ''}
              </div>
            </div>

            <!-- Items Container -->
            <div class="order-items-container">
              ${order.items.map(item => `
                <div class="order-item-row">
                  <img 
                    src="${item.product_image_url}" 
                    alt="${item.product_title}" 
                    class="order-item-thumb" 
                    onerror="this.src='https://images.unsplash.com/photo-1513519245088-0e12902e5a38?w=200&auto=format&fit=crop&q=60'"
                  />
                  <div style="flex: 1;">
                    <div style="font-weight: 700; color: var(--secondary); font-size: 0.95rem;">
                      ${item.product_title}
                    </div>
                    <div style="font-size: 0.85rem; color: var(--text-muted); margin-top: 0.2rem;">
                      Sold by: <strong>${item.seller_username || 'Artisan Seller'}</strong> | Qty: ${item.quantity} × $${parseFloat(item.price).toFixed(2)}
                    </div>
                  </div>
                  <div style="font-weight: 800; font-size: 1.05rem; color: var(--secondary);">
                    $${parseFloat(item.subtotal).toFixed(2)}
                  </div>
                </div>
              `).join('')}
            </div>

            <!-- Shipping Summary -->
            <div class="order-shipping-summary">
              <div>
                <strong>Shipping to:</strong> ${order.full_name} — ${order.shipping_address}, ${order.city} ${order.postal_code} (Tel: ${order.phone})
              </div>
              <div style="color: var(--text-muted); font-size: 0.8rem;">
                Updated: ${formatDate(order.updated_at)}
              </div>
            </div>
          </div>
        `).join('')}
      </div>
    `;

  } catch (err) {
    if (err.status === 401 || err.status === 403) {
      container.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-icon">🔒</div>
          <h3>Please Sign In</h3>
          <p>Sign in to view your order history and tracking updates.</p>
          <a href="/login/?next=/orders/" class="btn btn-primary btn-lg">Sign In</a>
        </div>
      `;
    } else {
      container.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-icon">⚠️</div>
          <h3>Unable to Load Orders</h3>
          <p>${err.message || 'Please refresh the page and try again.'}</p>
        </div>
      `;
    }
  }
}

// Customer cancel order handler
async function cancelCustomerOrder(orderId) {
  if (!confirm(`Are you sure you want to cancel Order #${orderId}? Stock will be returned.`)) return;

  try {
    await apiRequest(`/api/orders/${orderId}/status/`, 'PATCH', { status: 'Cancelled' });
    showToast(`Order #${orderId} has been cancelled.`, 'info');
    initOrdersPage();
  } catch (err) {
    showToast(err.data?.detail || err.message || 'Could not cancel order.', 'error');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('checkout-form')) {
    initCheckoutPage();
  }
  if (document.getElementById('orders-page-container')) {
    initOrdersPage();
  }
});

