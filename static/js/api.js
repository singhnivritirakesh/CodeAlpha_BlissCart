/**
 * Bliss Card - API Helper & Utilities
 * Handles CSRF tokens, unified fetch requests, and Toast notifications.
 */

// Global User State
window.currentUser = null;

// Helper to retrieve cookie by name
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

// Ensure CSRF token is available
async function ensureCsrfToken() {
  let token = getCookie('csrftoken');
  if (!token) {
    try {
      const res = await fetch('/api/auth/csrf/', { credentials: 'same-origin' });
      const data = await res.json();
      token = data.csrfToken || getCookie('csrftoken');
    } catch (e) {
      console.warn('Could not refresh CSRF token automatically:', e);
    }
  }
  return token;
}

// Unified API caller
async function apiRequest(endpoint, method = 'GET', body = null) {
  const headers = {
    'Accept': 'application/json',
  };

  const isFormData = body instanceof FormData;
  if (!isFormData && body !== null) {
    headers['Content-Type'] = 'application/json';
  }

  // Attach CSRF for non-safe HTTP methods
  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method.toUpperCase())) {
    const csrfToken = await ensureCsrfToken();
    if (csrfToken) {
      headers['X-CSRFToken'] = csrfToken;
    }
  }

  const options = {
    method,
    headers,
    credentials: 'same-origin', // Required for session cookie handling
  };

  if (body !== null) {
    options.body = isFormData ? body : JSON.stringify(body);
  }

  try {
    const response = await fetch(endpoint, options);
    const contentType = response.headers.get('content-type');
    let data = null;

    if (contentType && contentType.includes('application/json')) {
      data = await response.json();
    } else {
      data = await response.text();
    }

    if (!response.ok) {
      const error = new Error(data?.message || data?.detail || 'Request failed');
      error.status = response.status;
      error.data = data;
      throw error;
    }

    return data;
  } catch (err) {
    console.error(`API Error on [${method}] ${endpoint}:`, err);
    throw err;
  }
}

// Toast notification helper
function showToast(message, type = 'info', duration = 4000) {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <span>${message}</span>
    <button style="background:none;border:none;color:white;cursor:pointer;font-size:1.1rem;" onclick="this.parentElement.remove()">✕</button>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

// Update UI based on authenticated user
function updateNavForUser(user) {
  window.currentUser = user;
  const authNav = document.getElementById('nav-auth-container');
  const mobileAuthNav = document.getElementById('mobile-nav-auth-container');

  if (!authNav) return;

  if (user) {
    const roleBadgeClass = user.role === 'admin' ? 'badge-admin' : (user.role === 'seller' ? 'badge-seller' : 'badge-buyer');
    const roleLabel = user.role.toUpperCase();

    let dashboardLink = '';
    if (user.role === 'admin') {
      dashboardLink = `<a href="/admin-dashboard/" class="btn btn-sm btn-outline">Admin Panel</a>`;
    } else if (user.role === 'seller') {
      dashboardLink = `<a href="/seller-dashboard/" class="btn btn-sm btn-outline">Seller Hub</a>`;
    }

    const html = `
      <div style="display:flex;align-items:center;gap:0.75rem;">
        ${dashboardLink}
        <span class="badge ${roleBadgeClass}">${roleLabel}</span>
        <span style="font-weight:600;font-size:0.9rem;">${user.username}</span>
        <button class="btn btn-sm btn-outline" onclick="handleLogout()">Logout</button>
      </div>
    `;

    authNav.innerHTML = html;
    if (mobileAuthNav) {
      mobileAuthNav.innerHTML = `
        <li style="padding:0.5rem 0;border-top:1px solid var(--border);">
          <div style="margin-bottom:0.5rem;">Signed in as <strong>${user.username}</strong> (<span class="badge ${roleBadgeClass}">${roleLabel}</span>)</div>
          ${dashboardLink ? `<div style="margin-bottom:0.5rem;">${dashboardLink}</div>` : ''}
          <button class="btn btn-sm btn-outline btn-block" onclick="handleLogout()">Logout</button>
        </li>
      `;
    }
  } else {
    const html = `
      <a href="/login/" class="btn btn-sm btn-outline">Login</a>
      <a href="/register/" class="btn btn-sm btn-primary">Sign Up</a>
    `;
    authNav.innerHTML = html;
    if (mobileAuthNav) {
      mobileAuthNav.innerHTML = `
        <li style="display:flex;gap:0.5rem;padding-top:0.5rem;border-top:1px solid var(--border);">
          <a href="/login/" class="btn btn-sm btn-outline" style="flex:1;">Login</a>
          <a href="/register/" class="btn btn-sm btn-primary" style="flex:1;">Sign Up</a>
        </li>
      `;
    }
  }
}

// Fetch session user on startup
async function checkAuthSession() {
  try {
    const data = await apiRequest('/api/auth/me/');
    if (data.authenticated) {
      updateNavForUser(data.user);
    } else {
      updateNavForUser(null);
    }
  } catch (err) {
    updateNavForUser(null);
  }
}

// Global logout handler
async function handleLogout() {
  try {
    await apiRequest('/api/auth/logout/', 'POST');
    showToast('Logged out successfully.', 'info');
    setTimeout(() => {
      window.location.href = '/login/';
    }, 600);
  } catch (err) {
    showToast('Logout failed. Please try again.', 'error');
  }
}

// Toggle mobile navigation menu
function toggleMobileMenu() {
  const menu = document.getElementById('mobile-menu');
  if (menu) {
    menu.classList.toggle('show');
  }
}

// Run on page DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
  ensureCsrfToken();
  checkAuthSession();
});

