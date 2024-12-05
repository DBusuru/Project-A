function addToCart(productId) {
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    fetch('/cart/add/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken,
        },
        body: JSON.stringify({
            'product_id': productId,
            'quantity': 1
        })
    })
    .then(response => {
        if (!response.ok) {
            return response.text().then(text => {
                throw new Error(`Server responded with ${response.status}: ${text}`);
            });
        }
        return response.json();
    })
    .then(data => {
        console.log('Success:', data);

        // Update all qty elements in the header
        const qtyElements = document.querySelectorAll('.qty');
        qtyElements.forEach(element => {
            element.textContent = data.cart_count;
        });

        // Update the badge if it exists
        const badgeElements = document.querySelectorAll('.badge.bg-danger');
        badgeElements.forEach(element => {
            element.textContent = data.cart_count;
        });

        // Update cart items count in the summary
        const cartSummaryElements = document.querySelectorAll('.cart-summary small');
        cartSummaryElements.forEach(element => {
            element.textContent = `${data.cart_count} Item(s) selected`;
        });

        alert('Product added to cart successfully!');
        
        // Optionally refresh the page or update the cart dropdown
        // location.reload();
    })
    .catch(error => {
        console.error('Error details:', error);
        alert(`Error adding product to cart: ${error.message}`);
    });
}