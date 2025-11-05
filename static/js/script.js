document.addEventListener("DOMContentLoaded", () => {
    // --- START FIREBASE CONFIG ---
    const firebaseConfig = {
        // ... PASTE YOUR FIREBASE CONFIG HERE ...
    };
    firebase.initializeApp(firebaseConfig);
    // ... (Your auth logic) ...

    const customerForm = document.getElementById("customer-form");
    const leadForm = document.getElementById("lead-form"); // NEW
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

    // Handle Lead Form (Epic 3.1) - NEW BLOCK
    if (leadForm) {
        leadForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const leadData = {
                name: document.getElementById("lead-name").value,
                email: document.getElementById("lead-email").value,
                source: document.getElementById("lead-source").value,
                status: "New" // Default status
            };

            const response = await fetch('/api/lead', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(leadData)
            });

            if (response.ok) {
                alert('New Lead captured!');
                leadForm.reset();
            } else {
                const errorData = await response.json();
                alert(`Error capturing lead: ${errorData.error || response.statusText}`);
            }
        });
    }
    // END NEW BLOCK

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