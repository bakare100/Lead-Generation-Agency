// AILeadGen Frontend JavaScript

// Global utility functions
function showAlert(message, type = 'info', duration = 5000) {
    // Remove existing alerts
    const existingAlerts = document.querySelectorAll('.alert-custom');
    existingAlerts.forEach(alert => alert.remove());

    // Create alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show alert-custom`;
    alertDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    `;
    
    alertDiv.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="fas ${getAlertIcon(type)} me-2"></i>
            <div>${message}</div>
            <button type="button" class="btn-close ms-auto" data-bs-dismiss="alert"></button>
        </div>
    `;

    // Add to document
    document.body.appendChild(alertDiv);

    // Auto dismiss after duration
    if (duration > 0) {
        setTimeout(() => {
            if (alertDiv && alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, duration);
    }

    // Add animation
    requestAnimationFrame(() => {
        alertDiv.classList.add('slide-up');
    });
}

function getAlertIcon(type) {
    const icons = {
        'success': 'fa-check-circle',
        'danger': 'fa-exclamation-circle',
        'warning': 'fa-exclamation-triangle',
        'info': 'fa-info-circle',
        'primary': 'fa-info-circle'
    };
    return icons[type] || 'fa-info-circle';
}

function showLoading(message = 'Loading...') {
    // Remove existing loading overlay
    hideLoading();

    const loadingDiv = document.createElement('div');
    loadingDiv.id = 'loadingOverlay';
    loadingDiv.className = 'loading-overlay';
    loadingDiv.innerHTML = `
        <div class="loading-content">
            <div class="spinner-border text-primary mb-3" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <h5>${message}</h5>
        </div>
    `;

    document.body.appendChild(loadingDiv);
    document.body.style.overflow = 'hidden';
}

function hideLoading() {
    const loadingDiv = document.getElementById('loadingOverlay');
    if (loadingDiv) {
        loadingDiv.remove();
        document.body.style.overflow = '';
    }
}

// Format numbers with commas
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

// Format currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(amount);
}

// Format date
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    } catch (error) {
        return 'Invalid Date';
    }
}

// Format relative time
function formatRelativeTime(dateString) {
    if (!dateString) return 'N/A';
    
    try {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMins / 60);
        const diffDays = Math.floor(diffHours / 24);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
        if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
        if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
        
        return formatDate(dateString);
    } catch (error) {
        return 'Invalid Date';
    }
}

// API helper functions
async function apiRequest(url, options = {}) {
    try {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            }
        };

        const finalOptions = { ...defaultOptions, ...options };
        
        const response = await fetch(url, finalOptions);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || `HTTP error! status: ${response.status}`);
        }
        
        return data;
    } catch (error) {
        console.error('API request failed:', error);
        throw error;
    }
}

// File upload helper
function handleFileUpload(file, onProgress = null) {
    return new Promise((resolve, reject) => {
        const formData = new FormData();
        formData.append('file', file);

        const xhr = new XMLHttpRequest();

        if (onProgress) {
            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable) {
                    const percentComplete = (e.loaded / e.total) * 100;
                    onProgress(percentComplete);
                }
            });
        }

        xhr.addEventListener('load', () => {
            if (xhr.status === 200) {
                try {
                    const response = JSON.parse(xhr.responseText);
                    resolve(response);
                } catch (error) {
                    reject(new Error('Invalid JSON response'));
                }
            } else {
                reject(new Error(`Upload failed with status: ${xhr.status}`));
            }
        });

        xhr.addEventListener('error', () => {
            reject(new Error('Upload failed due to network error'));
        });

        xhr.open('POST', '/upload_leads');
        xhr.send(formData);
    });
}

// Local storage helpers
function saveToLocalStorage(key, data) {
    try {
        localStorage.setItem(key, JSON.stringify(data));
        return true;
    } catch (error) {
        console.error('Failed to save to localStorage:', error);
        return false;
    }
}

function loadFromLocalStorage(key, defaultValue = null) {
    try {
        const item = localStorage.getItem(key);
        return item ? JSON.parse(item) : defaultValue;
    } catch (error) {
        console.error('Failed to load from localStorage:', error);
        return defaultValue;
    }
}

function removeFromLocalStorage(key) {
    try {
        localStorage.removeItem(key);
        return true;
    } catch (error) {
        console.error('Failed to remove from localStorage:', error);
        return false;
    }
}

// Table sorting functionality
function initTableSorting(tableId) {
    const table = document.getElementById(tableId);
    if (!table) return;

    const headers = table.querySelectorAll('th[data-sortable]');
    
    headers.forEach(header => {
        header.style.cursor = 'pointer';
        header.innerHTML += ' <i class="fas fa-sort text-muted"></i>';
        
        header.addEventListener('click', () => {
            const column = header.dataset.sortable;
            const isAscending = header.classList.contains('sort-asc');
            
            // Reset all headers
            headers.forEach(h => {
                h.classList.remove('sort-asc', 'sort-desc');
                const icon = h.querySelector('i');
                if (icon) {
                    icon.className = 'fas fa-sort text-muted';
                }
            });
            
            // Set current header
            const icon = header.querySelector('i');
            if (isAscending) {
                header.classList.add('sort-desc');
                icon.className = 'fas fa-sort-down text-primary';
                sortTable(table, column, false);
            } else {
                header.classList.add('sort-asc');
                icon.className = 'fas fa-sort-up text-primary';
                sortTable(table, column, true);
            }
        });
    });
}

function sortTable(table, column, ascending = true) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    rows.sort((a, b) => {
        const aValue = getCellValue(a, column);
        const bValue = getCellValue(b, column);
        
        if (aValue === bValue) return 0;
        
        const comparison = aValue > bValue ? 1 : -1;
        return ascending ? comparison : -comparison;
    });
    
    rows.forEach(row => tbody.appendChild(row));
}

function getCellValue(row, column) {
    const cell = row.querySelector(`[data-value="${column}"]`);
    if (cell) {
        return cell.dataset.sortValue || cell.textContent.trim();
    }
    
    // Fallback to column index
    const columnIndex = parseInt(column) || 0;
    const cells = row.querySelectorAll('td');
    if (cells[columnIndex]) {
        return cells[columnIndex].textContent.trim();
    }
    
    return '';
}

// Real-time updates
function startRealTimeUpdates(interval = 30000) {
    setInterval(async () => {
        try {
            const stats = await apiRequest('/api/stats');
            updateDashboardStats(stats);
        } catch (error) {
            console.warn('Failed to fetch real-time updates:', error);
        }
    }, interval);
}

function updateDashboardStats(stats) {
    // Update stats numbers
    const statElements = {
        'total-clients': stats.total_clients,
        'active-clients': stats.active_clients,
        'remaining-quota': stats.remaining_quota,
        'monthly-revenue': formatCurrency(stats.monthly_revenue)
    };
    
    Object.entries(statElements).forEach(([id, value]) => {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    });
}

// Form validation
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return false;
    
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('is-invalid');
            isValid = false;
        } else {
            field.classList.remove('is-invalid');
        }
    });
    
    // Email validation
    const emailFields = form.querySelectorAll('input[type="email"]');
    emailFields.forEach(field => {
        if (field.value && !isValidEmail(field.value)) {
            field.classList.add('is-invalid');
            isValid = false;
        }
    });
    
    return isValid;
}

function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Copy to clipboard
function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            showAlert('Copied to clipboard!', 'success', 2000);
        }).catch(() => {
            fallbackCopyToClipboard(text);
        });
    } else {
        fallbackCopyToClipboard(text);
    }
}

function fallbackCopyToClipboard(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    document.body.appendChild(textArea);
    textArea.select();
    
    try {
        document.execCommand('copy');
        showAlert('Copied to clipboard!', 'success', 2000);
    } catch (error) {
        showAlert('Failed to copy to clipboard', 'danger');
    }
    
    document.body.removeChild(textArea);
}

// Confirm action modal
function confirmAction(message, onConfirm, onCancel = null) {
    const modalId = 'confirmActionModal';
    let modal = document.getElementById(modalId);
    
    if (!modal) {
        modal = document.createElement('div');
        modal.id = modalId;
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Confirm Action</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p id="confirmMessage"></p>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-primary" id="confirmButton">Confirm</button>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }
    
    document.getElementById('confirmMessage').textContent = message;
    
    const confirmButton = document.getElementById('confirmButton');
    const newConfirmButton = confirmButton.cloneNode(true);
    confirmButton.parentNode.replaceChild(newConfirmButton, confirmButton);
    
    newConfirmButton.addEventListener('click', () => {
        onConfirm();
        bootstrap.Modal.getInstance(modal).hide();
    });
    
    if (onCancel) {
        modal.addEventListener('hidden.bs.modal', onCancel, { once: true });
    }
    
    new bootstrap.Modal(modal).show();
}

// Initialize tooltips and popovers
function initBootstrapComponents() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

// Export functions for global use
window.AILeadGen = {
    showAlert,
    showLoading,
    hideLoading,
    formatNumber,
    formatCurrency,
    formatDate,
    formatRelativeTime,
    apiRequest,
    handleFileUpload,
    saveToLocalStorage,
    loadFromLocalStorage,
    removeFromLocalStorage,
    initTableSorting,
    startRealTimeUpdates,
    validateForm,
    copyToClipboard,
    confirmAction,
    initBootstrapComponents
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap components
    initBootstrapComponents();
    
    // Start real-time updates if on dashboard
    if (window.location.pathname === '/') {
        startRealTimeUpdates();
    }
    
    // Initialize table sorting for tables with sortable class
    document.querySelectorAll('table.sortable').forEach(table => {
        initTableSorting(table.id);
    });
    
    // Add smooth scrolling to anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Add fade-in animation to cards
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        setTimeout(() => {
            card.classList.add('fade-in');
        }, index * 100);
    });
});

// Handle offline/online status
window.addEventListener('online', () => {
    showAlert('Connection restored', 'success', 3000);
});

window.addEventListener('offline', () => {
    showAlert('No internet connection', 'warning', 5000);
});

// Error handling for unhandled errors
window.addEventListener('error', (e) => {
    console.error('Unhandled error:', e);
    showAlert('An unexpected error occurred', 'danger');
});

// Error handling for unhandled promise rejections
window.addEventListener('unhandledrejection', (e) => {
    console.error('Unhandled promise rejection:', e);
    showAlert('An unexpected error occurred', 'danger');
});
