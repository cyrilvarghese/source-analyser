/**
 * Shared Utility Functions
 * Common utilities for the File Cropper frontend
 */

import { CONFIG, ENV } from './config.js';

/**
 * API Utilities
 */
export const API = {
    /**
     * Make a GET request
     */
    async get(endpoint, options = {}) {
        try {
            const response = await fetch(endpoint, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    ...options.headers
                },
                ...options
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            }
            return await response.text();
        } catch (error) {
            console.error('API GET Error:', error);
            throw error;
        }
    },

    /**
     * Make a POST request
     */
    async post(endpoint, data, options = {}) {
        try {
            const isFormData = data instanceof FormData;
            const headers = {
                'Accept': 'application/json',
                ...(!isFormData && { 'Content-Type': 'application/json' }),
                ...options.headers
            };

            const response = await fetch(endpoint, {
                method: 'POST',
                headers,
                body: isFormData ? data : JSON.stringify(data),
                ...options
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            }
            return await response.text();
        } catch (error) {
            console.error('API POST Error:', error);
            throw error;
        }
    },

    /**
     * Make a DELETE request
     */
    async delete(endpoint, options = {}) {
        try {
            const response = await fetch(endpoint, {
                method: 'DELETE',
                headers: {
                    'Accept': 'application/json',
                    ...options.headers
                },
                ...options
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            }
            return await response.text();
        } catch (error) {
            console.error('API DELETE Error:', error);
            throw error;
        }
    }
};

/**
 * DOM Utilities
 */
export const DOM = {
    /**
     * Get element by ID with error handling
     */
    getElementById(id) {
        const element = document.getElementById(id);
        if (!element) {
            console.warn(`Element with ID '${id}' not found`);
        }
        return element;
    },

    /**
     * Create element with attributes and content
     */
    createElement(tag, attributes = {}, content = '') {
        const element = document.createElement(tag);

        Object.entries(attributes).forEach(([key, value]) => {
            if (key === 'className') {
                element.className = value;
            } else if (key === 'innerHTML') {
                element.innerHTML = value;
            } else {
                element.setAttribute(key, value);
            }
        });

        if (content) {
            element.textContent = content;
        }

        return element;
    },

    /**
     * Show/hide elements
     */
    show(element) {
        if (element) {
            element.style.display = '';
            element.classList.remove('hidden');
        }
    },

    hide(element) {
        if (element) {
            element.style.display = 'none';
            element.classList.add('hidden');
        }
    },

    /**
     * Toggle element visibility
     */
    toggle(element) {
        if (element) {
            if (element.style.display === 'none' || element.classList.contains('hidden')) {
                this.show(element);
            } else {
                this.hide(element);
            }
        }
    }
};

/**
 * File Utilities
 */
export const FileUtils = {
    /**
     * Validate file type
     */
    isValidFileType(file) {
        const extension = '.' + file.name.split('.').pop().toLowerCase();
        return CONFIG.UI.ALLOWED_FILE_TYPES.includes(extension);
    },

    /**
     * Validate file size
     */
    isValidFileSize(file) {
        return file.size <= CONFIG.UI.MAX_FILE_SIZE;
    },

    /**
     * Format file size
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';

        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));

        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },

    /**
     * Get file extension
     */
    getFileExtension(filename) {
        return filename.split('.').pop().toLowerCase();
    }
};

/**
 * UI Utilities
 */
export const UI = {
    /**
     * Show toast notification
     */
    showToast(message, type = 'info', duration = CONFIG.UI.TOAST_DURATION) {
        const toast = DOM.createElement('div', {
            className: `toast toast-${type} fixed top-4 right-4 z-50 p-4 rounded shadow-lg`,
            innerHTML: message
        });

        document.body.appendChild(toast);

        // Animate in
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => {
            toast.style.opacity = '1';
            toast.style.transform = 'translateX(0)';
            toast.style.transition = 'all 0.3s ease';
        }, 10);

        // Remove after duration
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }, duration);
    },

    /**
     * Show loading spinner
     */
    showLoading(element, text = 'Loading...') {
        if (element) {
            element.innerHTML = `
                <div class="flex items-center justify-center">
                    <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                    <span class="ml-2">${text}</span>
                </div>
            `;
            element.disabled = true;
        }
    },

    /**
     * Hide loading spinner
     */
    hideLoading(element, originalContent = '') {
        if (element) {
            element.innerHTML = originalContent;
            element.disabled = false;
        }
    },

    /**
     * Debounce function calls
     */
    debounce(func, delay = CONFIG.UI.DEBOUNCE_DELAY) {
        let timeoutId;
        return function (...args) {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => func.apply(this, args), delay);
        };
    },

    /**
     * Throttle function calls
     */
    throttle(func, limit = 1000) {
        let inThrottle;
        return function (...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
};

/**
 * Storage Utilities
 */
export const Storage = {
    /**
     * Set item in localStorage with error handling
     */
    set(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (error) {
            console.error('Storage set error:', error);
            return false;
        }
    },

    /**
     * Get item from localStorage with error handling
     */
    get(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (error) {
            console.error('Storage get error:', error);
            return defaultValue;
        }
    },

    /**
     * Remove item from localStorage
     */
    remove(key) {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (error) {
            console.error('Storage remove error:', error);
            return false;
        }
    },

    /**
     * Clear all localStorage
     */
    clear() {
        try {
            localStorage.clear();
            return true;
        } catch (error) {
            console.error('Storage clear error:', error);
            return false;
        }
    }
};

/**
 * Validation Utilities
 */
export const Validator = {
    /**
     * Validate email format
     */
    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    },

    /**
     * Validate URL format
     */
    isValidURL(url) {
        try {
            new URL(url);
            return true;
        } catch {
            return false;
        }
    },

    /**
     * Check if string is empty or whitespace
     */
    isEmpty(value) {
        return !value || value.trim().length === 0;
    },

    /**
     * Validate required fields
     */
    validateRequired(fields) {
        const errors = [];
        Object.entries(fields).forEach(([key, value]) => {
            if (this.isEmpty(value)) {
                errors.push(`${key} is required`);
            }
        });
        return errors;
    }
};

/**
 * Date and Time Utilities
 */
export const DateTime = {
    /**
     * Format date to readable string
     */
    formatDate(date, options = {}) {
        const defaultOptions = {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        };

        return new Date(date).toLocaleDateString('en-US', { ...defaultOptions, ...options });
    },

    /**
     * Get relative time (e.g., "2 hours ago")
     */
    getRelativeTime(date) {
        const now = new Date();
        const diffInSeconds = Math.floor((now - new Date(date)) / 1000);

        if (diffInSeconds < 60) return 'just now';
        if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} minutes ago`;
        if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} hours ago`;
        return `${Math.floor(diffInSeconds / 86400)} days ago`;
    }
};

/**
 * Copy to clipboard utility
 */
export const Clipboard = {
    async copy(text) {
        try {
            if (navigator.clipboard && window.isSecureContext) {
                await navigator.clipboard.writeText(text);
                return true;
            } else {
                // Fallback for older browsers
                const textArea = document.createElement('textarea');
                textArea.value = text;
                textArea.style.position = 'fixed';
                textArea.style.left = '-999999px';
                textArea.style.top = '-999999px';
                document.body.appendChild(textArea);
                textArea.focus();
                textArea.select();
                document.execCommand('copy');
                textArea.remove();
                return true;
            }
        } catch (error) {
            console.error('Failed to copy to clipboard:', error);
            return false;
        }
    }
};

/**
 * Logger utility
 */
export const Logger = {
    log(message, data = null) {
        if (ENV.isDevelopment || CONFIG.FEATURES.ENABLE_DEBUG) {
            console.log(`[${new Date().toISOString()}] ${message}`, data || '');
        }
    },

    error(message, error = null) {
        console.error(`[${new Date().toISOString()}] ERROR: ${message}`, error || '');
    },

    warn(message, data = null) {
        if (ENV.isDevelopment || CONFIG.FEATURES.ENABLE_DEBUG) {
            console.warn(`[${new Date().toISOString()}] WARNING: ${message}`, data || '');
        }
    }
}; 