function initiateMpesaPayment(event) {
    event.preventDefault();
    
    const form = event.target;
    const phoneNumber = form.querySelector('#phone_number').value;
    
    // Show loading state
    const submitButton = form.querySelector('button[type="submit"]');
    const originalText = submitButton.innerHTML;
    submitButton.innerHTML = 'Processing...';
    submitButton.disabled = true;
    
    fetch(form.action, {
        method: 'POST',
        body: new FormData(form),
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Show success message
            showAlert('success', data.message);
            // Start polling for payment status
            pollPaymentStatus(data.transaction_id);
        } else {
            showAlert('error', data.message);
        }
    })
    .catch(error => {
        showAlert('error', 'An error occurred while processing your payment');
    })
    .finally(() => {
        // Reset button state
        submitButton.innerHTML = originalText;
        submitButton.disabled = false;
    });
}

function pollPaymentStatus(transactionId) {
    // Poll payment status every 5 seconds
    const interval = setInterval(() => {
        fetch(`/mpesa/status/${transactionId}/`)
            .then(response => response.json())
            .then(data => {
                if (data.status === 'completed') {
                    clearInterval(interval);
                    showAlert('success', 'Payment completed successfully!');
                    window.location.href = '/order/confirmation/';
                } else if (data.status === 'failed') {
                    clearInterval(interval);
                    showAlert('error', 'Payment failed. Please try again.');
                }
            });
    }, 5000);
    
    // Stop polling after 2 minutes
    setTimeout(() => clearInterval(interval), 120000);
}

function showAlert(type, message) {
    // Implement your alert UI here
} 