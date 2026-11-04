/**
 * Bliss Card - Shopping Cart Logic
 * Real-time quantity updates, removals, and persistent cart management.
 */

// Global function to update the navbar cart badge
async function refreshCartCount() {
  const badge = document.getElementById('cart-item-count');
  if (!badge) return;

  try {
    const cart = await apiRequest('/api/cart/');
    badge.innerText = cart.total_items || 0;
  } catch (err) {
    // If not authenticated or error, leave at 0
    badge.innerText = '0';
  }
}

// Load and render cart page
async function loadCartPage() {
  const container = document.getElementById('cart-page-container');
  if (!container) return;

  container.innerHTML = `
    <div style="text-align: center; padding: 4rem 0; color: var(--text-secondary);">
      <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">✦ Loading your cart...</div>
    </div>
  `;

  try {
    const cart = await apiRequest('/api/cart/');

    // Update navbar badge
    const badge = document.getElementById('cart-item-count');
    if (badge) badge.innerText = cart.total_items || 0;

    if (!cart.items || cart.items.length === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-icon">🛒</div>
          <h3>Your Shopping Cart is Empty</h3>
          <p>You haven't added any greeting cards to your cart yet. Explore our handcrafted collections!</p>
          <a href="/" class="btn btn-primary btn-lg">Browse Greeting Cards</a>
        </div>
      `;
      return;
    }

    const subtotalFormatted = parseFloat(cart.total_price).toFixed(2);

    container.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
        <h1 style="font-size: 1.75rem; font-weight: 800; color: var(--secondary);">
          Shopping Cart (${cart.total_items} items)
        </h1>
        <button class="btn btn-sm btn-outline" onclick="clearFullCart()">Clear Cart</button>
      </div>

      <div class="cart-layout">
        <!-- Cart Items List -->
        <div class="cart-table-card">
          ${cart.items.map(item => `
            <div class="cart-item-row" id="cart-item-${item.id}">
              <div class="cart-item-product-info">
                <img 
                  src="${item.product.image_display_url}" 
                  alt="${item.product.title}" 
                  class="cart-item-thumb" 
                  onerror="this.src='https://images.unsplash.com/photo-1513519245088-0e12902e5a38?w=200&auto=format&fit=crop&q=60'"
                />
                <div>
                  <a href="/products/${item.product.id}/" class="cart-item-title">
                    ${item.product.title}
                  </a>
                  <div class="cart-item-unit-price">
                    $${parseFloat(item.product.price).toFixed(2)} each 
                    ${item.product.stock <= 5 ? `<span style="color:var(--danger);font-weight:600;">(Only ${item.product.stock} left)</span>` : ''}
                  </div>
                </div>
              </div>

              <div class="cart-item-actions">
                <!-- Quantity modifier -->
                <div class="quantity-control">
                  <button 
                    type="button" 
                    class="quantity-btn" 
                    onclick="modifyItemQuantity(${item.id}, ${item.quantity - 1}, ${item.product.stock})"
                    title="Decrease quantity"
                  >−</button>
                  <input 
                    type="number" 
                    class="quantity-input" 
                    value="${item.quantity}" 
                    readonly 
                  />
                  <button 
                    type="button" 
                    class="quantity-btn" 
                    onclick="modifyItemQuantity(${item.id}, ${item.quantity + 1}, ${item.product.stock})"
                    title="Increase quantity"
                  >+</button>
                </div>

                <!-- Subtotal -->
                <div class="cart-item-subtotal">
                  $${parseFloat(item.subtotal).toFixed(2)}
                </div>

                <!-- Remove Button -->
                <button 
                  class="cart-item-remove-btn" 
                  onclick="removeCartItem(${item.id})"
                  title="Remove card from cart"
                  aria-label="Remove item"
                >
                  <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            </div>
          `).join('')}
        </div>

        <!-- Order Summary Card -->
        <div class="summary-card">
          <div class="summary-title">Order Summary</div>

          <div class="summary-row">
            <span>Items (${cart.total_items})</span>
            <span>$${subtotalFormatted}</span>
          </div>

          <div class="summary-row">
            <span>Standard Shipping</span>
            <span style="color: var(--success); font-weight: 600;">FREE</span>
          </div>

          <div class="summary-row">
            <span>Artisan Gift Packaging</span>
            <span style="color: var(--success); font-weight: 600;">Complimentary</span>
          </div>

          <div class="summary-row total-row">
            <span>Estimated Total</span>
            <span style="color: var(--primary);">$${subtotalFormatted}</span>
          </div>

          <div style="margin-top: 1.5rem; display: flex; flex-direction: column; gap: 0.75rem;">
            <a href="/checkout/" class="btn btn-primary btn-block btn-lg">
              Proceed to Checkout →
            </a>
            <a href="/" class="btn btn-outline btn-block">
              ← Continue Shopping
            </a>
          </div>
        </div>
      </div>
    `;

  } catch (err) {
    if (err.status === 401 || err.status === 403) {
      container.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-icon">🔒</div>
          <h3>Please Sign In</h3>
          <p>Sign in to view your shopping cart and complete your greeting card purchase.</p>
          <a href="/login/" class="btn btn-primary btn-lg">Sign In to Account</a>
        </div>
      `;
    } else {
      container.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-icon">⚠️</div>
          <h3>Unable to Load Cart</h3>
          <p>${err.message || 'Please refresh the page and try again.'}</p>
          <button class="btn btn-primary" onclick="loadCartPage()">Retry</button>
        </div>
      `;
    }
  }
}

// Modify item quantity
async function modifyItemQuantity(itemId, newQty, maxStock) {
  if (newQty < 1) {
    // If reduced to 0, ask to remove
    return removeCartItem(itemId);
  }

  if (newQty > maxStock) {
    showToast(`Sorry, only ${maxStock} items available in stock.`, 'warning');
    return;
  }

  try {
    await apiRequest(`/api/cart/items/${itemId}/`, 'PATCH', { quantity: newQty });
    loadCartPage();
    refreshCartCount();
  } catch (err) {
    showToast(err.data?.detail || err.message || 'Could not update quantity.', 'error');
  }
}

// Remove single cart item
async function removeCartItem(itemId) {
  try {
    await apiRequest(`/api/cart/items/${itemId}/`, 'DELETE');
    showToast('Item removed from cart.', 'info');
    loadCartPage();
    refreshCartCount();
  } catch (err) {
    showToast('Could not remove item.', 'error');
  }
}

// Clear all items from cart
async function clearFullCart() {
  if (!confirm('Are you sure you want to empty your entire cart?')) return;

  try {
    await apiRequest('/api/cart/clear/', 'DELETE');
    showToast('Cart cleared.', 'info');
    loadCartPage();
    refreshCartCount();
  } catch (err) {
    showToast('Could not clear cart.', 'error');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  // Always refresh count for the navbar
  refreshCartCount();

  // If on cart page, load full cart
  if (document.getElementById('cart-page-container')) {
    loadCartPage();
  }
});

