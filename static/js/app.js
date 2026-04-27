// OvernightApp JavaScript

// Theme Management (Auto/Smart Mode by default)
(function() {
    const THEME_KEY = 'overnight-theme';
    const THEMES = {
        AUTO: 'auto',
        LIGHT: 'light',
        DARK: 'dark'
    };

    function getSystemTheme() {
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }

    function getStoredTheme() {
        return localStorage.getItem(THEME_KEY) || THEMES.AUTO;
    }

    function getEffectiveTheme(storedTheme) {
        return storedTheme === THEMES.AUTO ? getSystemTheme() : storedTheme;
    }

    function applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
    }

    function updateThemeIcon(storedTheme) {
        const btn = document.getElementById('theme-toggle');
        if (!btn) return;

        const icons = {
            [THEMES.AUTO]: '🌗',
            [THEMES.LIGHT]: '☀️',
            [THEMES.DARK]: '🌙'
        };
        btn.textContent = icons[storedTheme] || icons[THEMES.AUTO];
        btn.title = `Theme: ${storedTheme}`;
    }

    function cycleTheme() {
        const stored = getStoredTheme();
        const next = stored === THEMES.AUTO ? THEMES.LIGHT :
                    stored === THEMES.LIGHT ? THEMES.DARK : THEMES.AUTO;

        localStorage.setItem(THEME_KEY, next);
        const effective = getEffectiveTheme(next);
        applyTheme(effective);
        updateThemeIcon(next);
    }

    // Initialize theme on page load
    const storedTheme = getStoredTheme();
    const effectiveTheme = getEffectiveTheme(storedTheme);
    applyTheme(effectiveTheme);

    // Update theme icon when DOM is ready
    document.addEventListener('DOMContentLoaded', () => updateThemeIcon(storedTheme));

    // Listen for system theme changes when in auto mode
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        if (getStoredTheme() === THEMES.AUTO) {
            applyTheme(e.matches ? 'dark' : 'light');
        }
    });

    // Expose cycle function globally
    window.toggleTheme = cycleTheme;
})();

document.addEventListener('DOMContentLoaded', function() {
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Form validation feedback
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // Confirmation dialogs for delete actions
    const deleteButtons = document.querySelectorAll('[data-confirm-delete]');
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(event) {
            const message = button.getAttribute('data-confirm-message') ||
                          'Are you sure you want to delete this item?';
            if (!confirm(message)) {
                event.preventDefault();
            }
        });
    });
});

// Utility function for AJAX requests
function csrfSafeMethod(method) {
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

// Get CSRF token from cookie
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

// Setup CSRF token for AJAX requests (for future use)
const csrftoken = getCookie('csrftoken');
