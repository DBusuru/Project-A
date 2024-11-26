function updateCartCount(count) {
    const cartBadge = document.querySelector('.cart-badge');
    if (count > 0) {
        if (cartBadge) {
            cartBadge.textContent = count;
        } else {
            const cartLink = document.querySelector('.cart-link');
            const badge = document.createElement('span');
            badge.className = 'badge bg-danger cart-badge';
            badge.textContent = count;
            cartLink.appendChild(badge);
        }
    } else {
        if (cartBadge) {
            cartBadge.remove();
        }
    }
}

// Update your existing add-to-cart AJAX call:
fetch('/add-to-cart/', {
    method: 'POST',
    // ... other fetch options ...
})
.then(response => response.json())
.then(data => {
    if (data.success) {
        updateCartCount(data.cart_count);
    }
});