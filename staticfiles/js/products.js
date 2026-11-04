/**
 * Bliss Card - Product Catalog & Details Logic
 */

let activeCategory = 'all';
let searchQuery = '';
let currentSort = 'newest';
let searchDebounceTimer = null;

// Load and render category pills
async function loadCategories() {
  const container = document.getElementById('category-pills-container');
  if (!container) return;

  try {
    const categories = await apiRequest('/api/categories/');
    let html = `
      <button class="category-pill ${activeCategory === 'all' ? 'active' : ''}" onclick="selectCategory('all')">
        All Cards
      </button>
    `;

    categories.forEach(cat => {
      html += `
        <button class="category-pill ${activeCategory === cat.slug ? 'active' : ''}" onclick="selectCategory('${cat.slug}')">
          ${cat.name} (${cat.product_count})
        </button>
      `;
    });

    container.innerHTML = html;
  } catch (err) {
    console.error('Failed to load categories:', err);
  }
}

// Select Category Handler
function selectCategory(categorySlug) {
  activeCategory = categorySlug;
  const pills = document.querySelectorAll('.category-pill');
  pills.forEach(p => p.classList.remove('active'));

  const buttons = document.querySelectorAll('#category-pills-container button');
  buttons.forEach(btn => {
    if (btn.getAttribute('onclick')?.includes(`'${categorySlug}'`)) {
      btn.classList.add('active');
    }
  });

  loadProducts();
}

// Fetch and render products with active filters
async function loadProducts() {
  const grid = document.getElementById('products-grid');
  if (!grid) return;

  grid.innerHTML = `
    <div style="grid-column: 1 / -1; text-align: center; padding: 3rem 0; color: var(--text-secondary);">
      <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">✦ Loading cards...</div>
    </div>
  `;

  let url = `/api/products/?ordering=${encodeURIComponent(currentSort)}`;
  if (activeCategory && activeCategory !== 'all') {
    url += `&category=${encodeURIComponent(activeCategory)}`;
  }
  if (searchQuery.trim()) {
    url += `&search=${encodeURIComponent(searchQuery.trim())}`;
  }

  try {
    const products = await apiRequest(url);

    if (products.length === 0) {
      grid.innerHTML = `
        <div style="grid-column: 1 / -1;">
          <div class="empty-state">
            <div class="empty-state-icon">💌</div>
            <h3>No Cards Found</h3>
            <p>We couldn't find any greeting cards matching your current filter or search criteria.</p>
            <button class="btn btn-primary" onclick="resetFilters()">Clear Filters</button>
          </div>
        </div>
      `;
      return;
    }

    grid.innerHTML = products.map(product => `
      <div class="product-card">
        <a href="/products/${product.id}/" class="product-img-wrapper">
          <img 
            src="${product.image_display_url}" 
            alt="${product.title}" 
            class="product-img" 
            loading="lazy" 
            onerror="this.src='https://images.unsplash.com/photo-1513519245088-0e12902e5a38?w=500&auto=format&fit=crop&q=60'"
          />
          <div class="product-badge-overlay">
            ${product.is_in_stock 
              ? `<span class="badge" style="background: rgba(255,255,255,0.95); color: #047857; font-size:0.7rem;">In Stock</span>` 
              : `<span class="badge" style="background: rgba(239,68,68,0.9); color: white; font-size:0.7rem;">Sold Out</span>`}
          </div>
        </a>

        <div class="product-card-body">
          <div class="product-category-name">${product.category?.name || 'General'}</div>
          <a href="/products/${product.id}/" class="product-title" title="${product.title}">
            ${product.title}
          </a>
          <div class="product-seller-credit">
            Artisan: <strong>${product.seller?.username || 'Bliss Studio'}</strong>
          </div>

          <div class="product-card-footer">
            <div class="product-price">$${parseFloat(product.price).toFixed(2)}</div>
            <div>
              <a href="/products/${product.id}/" class="btn btn-sm btn-outline">Details</a>
              ${product.is_in_stock ? `
                <button 
                  class="btn btn-sm btn-primary" 
                  onclick="quickAddToCart(${product.id})"
                  title="Add to shopping cart"
                >
                  + Cart
                </button>
              ` : `
                <button class="btn btn-sm btn-outline" disabled style="opacity:0.5;">
                  Unavailable
                </button>
              `}
            </div>
          </div>
        </div>
      </div>
    `).join('');

  } catch (err) {
    grid.innerHTML = `
      <div style="grid-column: 1 / -1; text-align: center; padding: 2rem; color: var(--danger);">
        Failed to load cards. Please verify connection and try again.
      </div>
    `;
  }
}

// Reset all filters
function resetFilters() {
  activeCategory = 'all';
  searchQuery = '';
  currentSort = 'newest';

  const searchInput = document.getElementById('search-input');
  if (searchInput) searchInput.value = '';

  const sortSelect = document.getElementById('sort-select');
  if (sortSelect) sortSelect.value = 'newest';

  loadCategories();
  loadProducts();
}

// Quick Add To Cart function (stub wired to Cart API in Stage 4)
async function quickAddToCart(productId) {
  try {
    await apiRequest('/api/cart/items/', 'POST', {
      product_id: productId,
      quantity: 1
    });
    showToast('Card added to your cart!', 'success');
    if (typeof refreshCartCount === 'function') {
      refreshCartCount();
    }
  } catch (err) {
    if (err.status === 401 || err.status === 403) {
      showToast('Please sign in to add items to your cart.', 'info');
      setTimeout(() => { window.location.href = '/login/'; }, 1000);
    } else {
      showToast(err.data?.detail || err.message || 'Could not add to cart.', 'error');
    }
  }
}

// Product Detail Page Initialization
async function initProductDetailPage() {
  const container = document.getElementById('product-detail-container');
  if (!container) return;

  // Extract ID from pathname: /products/12/
  const match = window.location.pathname.match(/\/products\/(\d+)\/?/);
  if (!match) {
    container.innerHTML = '<div class="empty-state"><h3>Invalid Product URL</h3></div>';
    return;
  }

  const productId = match[1];

  try {
    const product = await apiRequest(`/api/products/${productId}/`);

    // Update document title
    document.title = `${product.title} - Bliss Card`;

    container.innerHTML = `
      <div class="breadcrumbs">
        <a href="/">Home</a> <span>/</span>
        <a href="/?category=${product.category?.slug || ''}">${product.category?.name || 'Cards'}</a> <span>/</span>
        <span style="color: var(--text-primary); font-weight: 500;">${product.title}</span>
      </div>

      <div class="detail-layout">
        <div class="detail-img-box">
          <img 
            src="${product.image_display_url}" 
            alt="${product.title}" 
            onerror="this.src='https://images.unsplash.com/photo-1513519245088-0e12902e5a38?w=700&auto=format&fit=crop&q=80'"
          />
        </div>

        <div class="detail-info">
          <div style="display:flex; justify-content:space-between; align-items:flex-start;">
            <span class="badge badge-seller" style="margin-bottom: 0.5rem;">
              ${product.category?.name || 'Exclusive Design'}
            </span>
            ${product.is_in_stock 
              ? `<span class="stock-tag in-stock">● ${product.stock} in stock</span>` 
              : `<span class="stock-tag out-of-stock">● Out of stock</span>`}
          </div>

          <h1 class="detail-title">${product.title}</h1>

          <div style="font-size: 0.9rem; color: var(--text-secondary); margin-bottom: 0.5rem;">
            Designed & crafted by <strong>${product.seller?.username || 'Artisan'}</strong>
          </div>

          <div class="detail-price-box">
            <span class="detail-price">$${parseFloat(product.price).toFixed(2)}</span>
            <span style="font-size: 0.85rem; color: var(--text-muted);">Includes eco-friendly envelope & wax seal</span>
          </div>

          <div style="margin-bottom: 1.5rem;">
            <h4 style="font-size: 0.95rem; font-weight: 700; margin-bottom: 0.4rem; color: var(--secondary);">Description</h4>
            <p style="color: var(--text-secondary); line-height: 1.7; font-size: 0.95rem; white-space: pre-line;">
              ${product.description}
            </p>
          </div>

          <!-- Purchase Controls -->
          ${product.is_in_stock ? `
            <div style="background: var(--bg-surface); border: 1px solid var(--border); padding: 1.25rem; border-radius: var(--radius-md); margin-top: auto;">
              <label class="form-label">Quantity</label>
              <div style="display: flex; gap: 1rem; align-items: center; flex-wrap: wrap;">
                <div class="quantity-control">
                  <button type="button" class="quantity-btn" onclick="stepQuantity(-1)">−</button>
                  <input type="number" id="detail-qty-input" class="quantity-input" value="1" min="1" max="${product.stock}" readonly />
                  <button type="button" class="quantity-btn" onclick="stepQuantity(1, ${product.stock})">+</button>
                </div>
                <button 
                  class="btn btn-primary btn-lg" 
                  style="flex: 1;" 
                  id="add-to-cart-detail-btn"
                  onclick="submitAddToCart(${product.id})"
                >
                  Add to Cart ✦ $${parseFloat(product.price).toFixed(2)}
                </button>
              </div>
            </div>
          ` : `
            <div style="background: var(--danger-light); border: 1px solid var(--danger); padding: 1.25rem; border-radius: var(--radius-md); color: var(--danger); text-align: center; margin-top: auto;">
              <strong>Currently Out of Stock</strong>
              <p style="font-size: 0.85rem; margin-top: 0.25rem;">This handcrafted card is currently sold out. Check back soon for restocks.</p>
            </div>
          `}
        </div>
      </div>
    `;

  } catch (err) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">🔍</div>
        <h3>Card Not Found</h3>
        <p>The greeting card you requested does not exist or may have been removed.</p>
        <a href="/" class="btn btn-primary">Return to Shop</a>
      </div>
    `;
  }
}

// Step quantity helper
function stepQuantity(delta, maxStock = 99) {
  const input = document.getElementById('detail-qty-input');
  if (!input) return;
  let val = parseInt(input.value) || 1;
  val += delta;
  if (val < 1) val = 1;
  if (val > maxStock) val = maxStock;
  input.value = val;
}

// Add to cart from detail page
async function submitAddToCart(productId) {
  const input = document.getElementById('detail-qty-input');
  const qty = input ? parseInt(input.value) : 1;
  const btn = document.getElementById('add-to-cart-detail-btn');

  if (btn) {
    btn.disabled = true;
    btn.innerText = 'Adding...';
  }

  try {
    await apiRequest('/api/cart/items/', 'POST', {
      product_id: productId,
      quantity: qty
    });
    showToast(`Added ${qty} item(s) to your cart!`, 'success');
    if (typeof refreshCartCount === 'function') {
      refreshCartCount();
    }
  } catch (err) {
    if (err.status === 401 || err.status === 403) {
      showToast('Please sign in to add cards to your cart.', 'info');
      setTimeout(() => { window.location.href = '/login/'; }, 1000);
    } else {
      showToast(err.data?.detail || err.message || 'Could not add to cart.', 'error');
    }
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerText = 'Add to Cart ✦';
    }
  }
}

// Setup search input debounce & sort listener
function initCatalogListeners() {
  const searchInput = document.getElementById('search-input');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      clearTimeout(searchDebounceTimer);
      searchDebounceTimer = setTimeout(() => {
        searchQuery = e.target.value;
        loadProducts();
      }, 300);
    });
  }

  const sortSelect = document.getElementById('sort-select');
  if (sortSelect) {
    sortSelect.addEventListener('change', (e) => {
      currentSort = e.target.value;
      loadProducts();
    });
  }
}

document.addEventListener('DOMContentLoaded', () => {
  // Check if we are on index/catalog page
  if (document.getElementById('products-grid')) {
    loadCategories();
    loadProducts();
    initCatalogListeners();
  }

  // Check if we are on detail page
  if (document.getElementById('product-detail-container')) {
    initProductDetailPage();
  }
});

