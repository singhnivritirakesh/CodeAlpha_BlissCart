/**
 * Bliss Card - Auth Handlers (Login, Registration, Form Validation)
 */

// Helper to clear error messages
function clearFormErrors(formId) {
  const form = document.getElementById(formId);
  if (!form) return;
  const errors = form.querySelectorAll('.form-error');
  errors.forEach(el => el.remove());
  const inputs = form.querySelectorAll('.form-control');
  inputs.forEach(input => input.style.borderColor = '');
}

// Helper to show field error
function setFieldError(fieldInput, message) {
  if (!fieldInput) return;
  fieldInput.style.borderColor = 'var(--danger)';
  const errSpan = document.createElement('span');
  errSpan.className = 'form-error';
  errSpan.innerText = message;
  fieldInput.parentElement.appendChild(errSpan);
}

// Quick fill credentials for easy testing
function fillDemoCredentials(username, password) {
  const userField = document.getElementById('login-username');
  const passField = document.getElementById('login-password');
  if (userField && passField) {
    userField.value = username;
    passField.value = password;
    showToast(`Filled credentials for ${username}`, 'info', 2000);
  }
}

// Setup Login Form Handler
function initLoginForm() {
  const form = document.getElementById('login-form');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearFormErrors('login-form');

    const username = document.getElementById('login-username').value.trim();
    const password = document.getElementById('login-password').value;
    const submitBtn = form.querySelector('button[type="submit"]');

    // Basic Client Validation
    let hasError = false;
    if (!username) {
      setFieldError(document.getElementById('login-username'), 'Username is required.');
      hasError = true;
    }
    if (!password) {
      setFieldError(document.getElementById('login-password'), 'Password is required.');
      hasError = true;
    }
    if (hasError) return;

    submitBtn.disabled = true;
    submitBtn.innerText = 'Signing in...';

    try {
      const response = await apiRequest('/api/auth/login/', 'POST', { username, password });
      showToast(response.message || 'Login successful!', 'success');

      // Update navbar state immediately
      updateNavForUser(response.user);

      // Redirect after brief delay
      setTimeout(() => {
        window.location.href = response.redirect_url || '/';
      }, 700);
    } catch (err) {
      submitBtn.disabled = false;
      submitBtn.innerText = 'Sign In';

      if (err.data) {
        if (typeof err.data === 'string') {
          showToast(err.data, 'error');
        } else if (err.data.non_field_errors) {
          showToast(err.data.non_field_errors[0], 'error');
        } else {
          for (const [field, messages] of Object.entries(err.data)) {
            const input = document.getElementById(`login-${field}`);
            if (input) {
              setFieldError(input, Array.isArray(messages) ? messages[0] : messages);
            } else {
              showToast(Array.isArray(messages) ? messages[0] : messages, 'error');
            }
          }
        }
      } else {
        showToast(err.message || 'Login failed.', 'error');
      }
    }
  });
}

// Setup Register Form Handler
function initRegisterForm() {
  const form = document.getElementById('register-form');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearFormErrors('register-form');

    const username = document.getElementById('reg-username').value.trim();
    const email = document.getElementById('reg-email').value.trim();
    const role = document.getElementById('reg-role').value;
    const password = document.getElementById('reg-password').value;
    const passwordConfirm = document.getElementById('reg-password-confirm').value;
    const phone = document.getElementById('reg-phone')?.value.trim() || '';
    const address = document.getElementById('reg-address')?.value.trim() || '';
    const submitBtn = form.querySelector('button[type="submit"]');

    // Client Validation
    let hasError = false;
    if (!username) {
      setFieldError(document.getElementById('reg-username'), 'Username is required.');
      hasError = true;
    }
    if (password.length < 6) {
      setFieldError(document.getElementById('reg-password'), 'Password must be at least 6 characters.');
      hasError = true;
    }
    if (password !== passwordConfirm) {
      setFieldError(document.getElementById('reg-password-confirm'), 'Passwords do not match.');
      hasError = true;
    }
    if (hasError) return;

    submitBtn.disabled = true;
    submitBtn.innerText = 'Creating account...';

    const payload = {
      username,
      email,
      role,
      password,
      password_confirm: passwordConfirm,
      phone_number: phone,
      address
    };

    try {
      const response = await apiRequest('/api/auth/register/', 'POST', payload);
      showToast(response.message || 'Account created successfully!', 'success');
      updateNavForUser(response.user);

      setTimeout(() => {
        if (response.user.role === 'seller') {
          window.location.href = '/seller-dashboard/';
        } else {
          window.location.href = '/';
        }
      }, 800);
    } catch (err) {
      submitBtn.disabled = false;
      submitBtn.innerText = 'Create Account';

      if (err.data && typeof err.data === 'object') {
        for (const [field, messages] of Object.entries(err.data)) {
          const fieldMap = {
            'username': 'reg-username',
            'email': 'reg-email',
            'role': 'reg-role',
            'password': 'reg-password',
            'password_confirm': 'reg-password-confirm',
            'phone_number': 'reg-phone',
            'address': 'reg-address',
          };
          const input = document.getElementById(fieldMap[field] || `reg-${field}`);
          if (input) {
            setFieldError(input, Array.isArray(messages) ? messages[0] : messages);
          } else {
            showToast(Array.isArray(messages) ? messages[0] : messages, 'error');
          }
        }
      } else {
        showToast(err.message || 'Registration failed.', 'error');
      }
    }
  });
}

document.addEventListener('DOMContentLoaded', () => {
  initLoginForm();
  initRegisterForm();
});

