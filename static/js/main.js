/* ============================================
    WellReserve - Main JavaScript
    ============================================ */

const APP_ASSET_VERSION = '20260609-3';

document.addEventListener('DOMContentLoaded', function() {
    
    // Fix offcanvas navbar display on desktop
    fixOffcanvasDesktopDisplay();
    fixOffcanvasDropdownPosition();
    resetStalePwaState();
    registerServiceWorker();
    
    // Initialize all components
    initTooltips();
    initAlerts();
    initForms();
    initCheckoutForm();
    initNavbar();
    initAnimations();
    initConfirmDialogs();
    
});

/* ============================================
   PWA Cache Reset
   ============================================ */
async function resetStalePwaState() {
    if (!('serviceWorker' in navigator) && !('caches' in window)) {
        return;
    }

    try {
        const storedVersion = localStorage.getItem('wellreserve-asset-version');
        if (storedVersion === APP_ASSET_VERSION) {
            return;
        }

        if ('serviceWorker' in navigator) {
            const registrations = await navigator.serviceWorker.getRegistrations();
            await Promise.all(registrations.map(function(registration) {
                return registration.unregister();
            }));
        }

        if ('caches' in window) {
            const cacheKeys = await caches.keys();
            await Promise.all(cacheKeys.map(function(cacheName) {
                return caches.delete(cacheName);
            }));
        }

        localStorage.setItem('wellreserve-asset-version', APP_ASSET_VERSION);
    } catch (error) {
        console.warn('Failed to reset stale PWA state:', error);
    }
}

/* ============================================
   Tooltips
   ============================================ */
function initTooltips() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/* ============================================
   Auto-dismiss Alerts
   ============================================ */
function initAlerts() {
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
}

/* ============================================
   Fix Offcanvas Display on Desktop
   ============================================ */
function fixOffcanvasDesktopDisplay() {
    // On desktop (lg+), make offcanvas always visible
    const offcanvas = document.querySelector('.offcanvas');
    if (!offcanvas) return;
    
    function updateOffcanvasDisplay() {
        const isDesktop = window.innerWidth >= 992;
        if (isDesktop) {
            // Show offcanvas permanently on desktop using setProperty for !important
            offcanvas.style.setProperty('visibility', 'visible', 'important');
            offcanvas.style.setProperty('position', 'relative', 'important');
            offcanvas.style.setProperty('width', '100%', 'important');
            offcanvas.style.setProperty('height', 'auto', 'important');
            offcanvas.style.setProperty('background-color', 'transparent', 'important');
            offcanvas.style.setProperty('border', 'none', 'important');
            // Hide the toggler button on desktop
            const toggler = document.querySelector('.navbar-toggler');
            if (toggler) toggler.style.setProperty('display', 'none', 'important');
        } else {
            // Restore mobile behavior
            offcanvas.style.removeProperty('visibility');
            offcanvas.style.removeProperty('position');
            offcanvas.style.removeProperty('width');
            offcanvas.style.removeProperty('height');
            offcanvas.style.removeProperty('background-color');
            offcanvas.style.removeProperty('border');
            const toggler = document.querySelector('.navbar-toggler');
            if (toggler) toggler.style.removeProperty('display');
        }
    }
    
    // Apply on load
    updateOffcanvasDisplay();
    
    // Update on resize
    window.addEventListener('resize', updateOffcanvasDisplay);
}

/* ============================================
   Fix Offcanvas Dropdown Position
   ============================================ */
function fixOffcanvasDropdownPosition() {
    const offcanvas = document.querySelector('.offcanvas');
    if (!offcanvas) return;

    const dropdownToggles = offcanvas.querySelectorAll('.dropdown-toggle');

    function clearDropdownMenuPosition(dropdown) {
        const menu = dropdown.querySelector('.dropdown-menu');
        if (!menu) return;

        menu.style.removeProperty('position');
        menu.style.removeProperty('top');
        menu.style.removeProperty('right');
        menu.style.removeProperty('left');
        menu.style.removeProperty('transform');
        menu.style.removeProperty('z-index');
    }

    function placeDropdownMenu(dropdown) {
        const menu = dropdown.querySelector('.dropdown-menu');
        if (!menu) return;

        menu.style.setProperty('position', 'absolute', 'important');
        menu.style.setProperty('top', '100%', 'important');
        menu.style.setProperty('right', '0', 'important');
        menu.style.setProperty('left', 'auto', 'important');
        menu.style.setProperty('transform', 'none', 'important');
        menu.style.setProperty('z-index', '1050', 'important');
    }

    dropdownToggles.forEach(function(toggle) {
        toggle.addEventListener('shown.bs.dropdown', function() {
            const dropdown = this.closest('.dropdown');
            if (!dropdown) return;

            if (window.innerWidth >= 992) {
                placeDropdownMenu(dropdown);
            } else {
                clearDropdownMenuPosition(dropdown);
            }
        });

        toggle.addEventListener('click', function() {
            const dropdown = this.closest('.dropdown');
            if (!dropdown) return;

            if (window.innerWidth >= 992) {
                window.setTimeout(function() {
                    placeDropdownMenu(dropdown);
                }, 0);
            } else {
                window.setTimeout(function() {
                    clearDropdownMenuPosition(dropdown);
                }, 0);
            }
        });
    });
}

/* ============================================
   Form Validation & Enhancement
   ============================================ */
function initForms() {
    // Add loading state to forms on submit
    const forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn && !submitBtn.classList.contains('no-loading')) {
                submitBtn.disabled = true;
                const originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>A processar...';
                
                // Re-enable after 10 seconds (fallback)
                setTimeout(function() {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalText;
                }, 10000);
            }
        });
    });
    
    // Date inputs - set min date to today for future-only inputs
    const dateInputs = document.querySelectorAll('input[type="date"].future-only');
    const today = new Date().toISOString().split('T')[0];
    dateInputs.forEach(function(input) {
        input.setAttribute('min', today);
    });
    
    // Phone number formatting
    const phoneInputs = document.querySelectorAll('input[name="telefone"]');
    phoneInputs.forEach(function(input) {
        input.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 9) {
                value = value.substring(0, 9);
            }
            e.target.value = value;
        });
    });
}

/* ============================================
   Checkout Form Enhancements
   ============================================ */
function initCheckoutForm() {
    const sameAddressCheckbox = document.getElementById('id_entrega_morada_igual_faturacao');
    const billingAddress = document.getElementById('id_faturacao_morada');
    const deliveryAddress = document.getElementById('id_entrega_morada');
    const deliveryGroup = document.getElementById('entrega-morada-group');
    const deliverySummary = document.getElementById('entrega-morada-summary');

    if (!sameAddressCheckbox || !billingAddress || !deliveryAddress || !deliveryGroup || !deliverySummary) {
        return;
    }

    const syncDeliveryAddress = function() {
        const isSame = sameAddressCheckbox.checked;

        deliveryGroup.classList.toggle('d-none', isSame);
        deliverySummary.classList.toggle('d-none', !isSame);
        deliveryAddress.disabled = isSame;

        if (isSame) {
            deliveryAddress.value = billingAddress.value;
            deliverySummary.innerHTML = `<strong>Morada de entrega:</strong> igual à morada de faturação.<br>${billingAddress.value.replace(/\n/g, '<br>')}`;
        } else {
            deliverySummary.innerHTML = '';
        }
    };

    sameAddressCheckbox.addEventListener('change', syncDeliveryAddress);
    billingAddress.addEventListener('input', function() {
        if (sameAddressCheckbox.checked) {
            deliveryAddress.value = billingAddress.value;
        }
    });

    syncDeliveryAddress();
}

/* ============================================
   Navbar Scroll Effect
   ============================================ */
function initNavbar() {
    const navbar = document.querySelector('.navbar');
    if (navbar) {
        window.addEventListener('scroll', function() {
            if (window.scrollY > 50) {
                navbar.classList.add('navbar-scrolled');
            } else {
                navbar.classList.remove('navbar-scrolled');
            }
        });
    }
}

/* ============================================
   Scroll Animations
   ============================================ */
function initAnimations() {
    const animatedElements = document.querySelectorAll('.animate-on-scroll');
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.1
    });
    
    animatedElements.forEach(function(el) {
        observer.observe(el);
    });
}

/* ============================================
   Confirm Dialogs
   ============================================ */
function initConfirmDialogs() {
    const confirmLinks = document.querySelectorAll('[data-confirm]');
    confirmLinks.forEach(function(link) {
        link.addEventListener('click', function(e) {
            const message = this.getAttribute('data-confirm') || 'Tem a certeza que deseja continuar?';
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });
}

/* ============================================
   PWA Service Worker
   ============================================ */
function registerServiceWorker() {
    if (!('serviceWorker' in navigator)) {
        return;
    }

    window.addEventListener('load', function() {
        navigator.serviceWorker.register('/sw.js?v=20260609-3').catch(function(error) {
            console.warn('Service worker registration failed:', error);
        });
    });
}

/* ============================================
   Toast Notifications
   ============================================ */
function showToast(message, type = 'info') {
    const toastContainer = document.querySelector('.toast-container') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}

function createToastContainer() {
    const container = document.createElement('div');
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    document.body.appendChild(container);
    return container;
}

/* ============================================
   Cart Functions
   ============================================ */
function updateCartCount(count) {
    const cartBadge = document.querySelector('.cart-badge');
    if (cartBadge) {
        cartBadge.textContent = count;
        if (count > 0) {
            cartBadge.style.display = 'inline-block';
        } else {
            cartBadge.style.display = 'none';
        }
    }
}

function addToCart(productId, quantity = 1) {
    fetch(`/carrinho/adicionar/${productId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ quantidade: quantity })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Produto adicionado ao carrinho!', 'success');
            updateCartCount(data.cart_count);
        } else {
            showToast(data.error || 'Erro ao adicionar produto', 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Erro ao adicionar produto', 'danger');
    });
}

/* ============================================
   Reservation Functions
   ============================================ */
function loadAvailableSlots(serviceId, date, employeeId = null) {
    let url = `/api/horarios-disponiveis/?servico=${serviceId}&data=${date}`;
    if (employeeId) {
        url += `&funcionario=${employeeId}`;
    }
    
    return fetch(url)
        .then(response => response.json())
        .then(data => {
            return data.horarios || [];
        })
        .catch(error => {
            console.error('Error loading slots:', error);
            return [];
        });
}

/* ============================================
   Utility Functions
   ============================================ */
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

function formatCurrency(value) {
    return new Intl.NumberFormat('pt-PT', {
        style: 'currency',
        currency: 'EUR'
    }).format(value);
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('pt-PT', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    }).format(date);
}

function formatTime(timeString) {
    return timeString.substring(0, 5);
}

/* ============================================
   Search Functionality
   ============================================ */
function initSearch() {
    const searchInput = document.querySelector('#searchInput');
    if (searchInput) {
        let timeout = null;
        searchInput.addEventListener('input', function(e) {
            clearTimeout(timeout);
            timeout = setTimeout(function() {
                performSearch(e.target.value);
            }, 300);
        });
    }
}

function performSearch(query) {
    if (query.length < 2) return;
    
    fetch(`/api/pesquisa/?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            displaySearchResults(data);
        })
        .catch(error => {
            console.error('Search error:', error);
        });
}

function displaySearchResults(results) {
    const resultsContainer = document.querySelector('#searchResults');
    if (!resultsContainer) return;
    
    resultsContainer.innerHTML = '';
    
    if (results.length === 0) {
        resultsContainer.innerHTML = '<p class="text-muted p-3">Nenhum resultado encontrado</p>';
        return;
    }
    
    results.forEach(function(item) {
        const div = document.createElement('div');
        div.className = 'search-result-item p-2 border-bottom';
        div.innerHTML = `
            <a href="${item.url}" class="text-decoration-none">
                <strong>${item.nome}</strong>
                <br>
                <small class="text-muted">${item.tipo}</small>
            </a>
        `;
        resultsContainer.appendChild(div);
    });
}

/* ============================================
   Print Functionality
   ============================================ */
function printElement(elementId) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
        <html>
        <head>
            <title>Imprimir</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                body { padding: 20px; }
                @media print {
                    .no-print { display: none; }
                }
            </style>
        </head>
        <body>
            ${element.innerHTML}
            <script>
                window.onload = function() {
                    window.print();
                    window.close();
                };
            </script>
        </body>
        </html>
    `);
    printWindow.document.close();
}

/* ============================================
   Export to CSV
   ============================================ */
function exportTableToCSV(tableId, filename) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    let csv = [];
    const rows = table.querySelectorAll('tr');
    
    rows.forEach(function(row) {
        const cols = row.querySelectorAll('td, th');
        const rowData = [];
        cols.forEach(function(col) {
            rowData.push('"' + col.innerText.replace(/"/g, '""') + '"');
        });
        csv.push(rowData.join(','));
    });
    
    const csvContent = csv.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename || 'export.csv';
    link.click();
}
