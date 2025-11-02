document.addEventListener("DOMContentLoaded", () => {
    // --- START FIREBASE CONFIG ---
    const firebaseConfig = {
        // ... PASTE YOUR FIREBASE CONFIG HERE ...
    };
    firebase.initializeApp(firebaseConfig);
    // ... (Your auth logic) ...

    const customerForm = document.getElementById("customer-form");
    const ticketCustomerSelect = document.getElementById("ticket-customer");

    // Handle Customer Form (Epic 2)
    if (customerForm) {
        customerForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const customerData = {
                name: document.getElementById("cust-name").value,
                email: document.getElementById("cust-email").value,
                phone: document.getElementById("cust-phone").value,
            };

            const response = await fetch('/api/customer', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(customerData)
            });

            if (response.ok) {
                alert('Customer created!');
                customerForm.reset();
                loadCustomers(); // Refresh the list
            } else {
                alert('Error creating customer.');
            }
        });
    }

    // Load customers into the dropdown (for Epic 4)
    async function loadCustomers() {
        if (!ticketCustomerSelect) return;
        
        const response = await fetch('/api/customers');
        if (!response.ok) return;

        const customers = await response.json();
        ticketCustomerSelect.innerHTML = '<option value="">Select a customer...</option>';
        customers.forEach(cust => {
            const option = document.createElement('option');
            option.value = cust.id;
            option.textContent = `${cust.name} (${cust.email})`;
            ticketCustomerSelect.appendChild(option);
        });
    }

    // Initial load
    loadCustomers();
});