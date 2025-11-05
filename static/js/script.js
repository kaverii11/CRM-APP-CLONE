// Wait for the DOM to be fully loaded before running scripts
document.addEventListener("DOMContentLoaded", () => {
    
    // --- 1. THEME TOGGLE (From Epic 10) ---
    const themeToggle = document.getElementById("theme-toggle");
    
    // Check for saved theme in localStorage and apply it
    const currentTheme = localStorage.getItem("theme");
    if (currentTheme === "dark") {
        document.documentElement.classList.add("dark-mode");
    }

    if (themeToggle) {
        themeToggle.addEventListener("click", () => {
            document.documentElement.classList.toggle("dark-mode");
            let theme = "light";
            if (document.documentElement.classList.contains("dark-mode")) {
                theme = "dark";
            }
            localStorage.setItem("theme", theme);
        });
    }

    // --- 2. MOBILE SIDEBAR TOGGLE ---
    const mobileMenuBtn = document.getElementById("mobile-menu-btn");
    
    if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener("click", () => {
            document.body.classList.toggle("sidebar-open");
        });
    }

    // --- 3. CUSTOMER PAGE LOGIC ---
    if (window.location.pathname === '/customers') {
        const addCustomerBtn = document.getElementById("add-customer-btn");
        const modal = document.getElementById("customer-modal");
        const modalCloseBtn = document.getElementById("modal-close-btn");
        const customerForm = document.getElementById("customer-form");
        const customersTableBody = document.getElementById("customers-table-body");
        const modalTitle = document.getElementById("modal-title");
        const customerIdField = document.getElementById("customer-id");

        const openModal = () => {
            modalTitle.textContent = "Add New Customer";
            customerForm.reset();
            customerIdField.value = "";
            modal.style.display = "flex";
        };

        const closeModal = () => {
            modal.style.display = "none";
        };

        addCustomerBtn.addEventListener("click", openModal);
        modalCloseBtn.addEventListener("click", closeModal);
        
        modal.addEventListener("click", (e) => {
            if (e.target === modal) {
                closeModal();
            }
        });

        async function loadCustomers() {
            try {
                const response = await fetch('/api/customers');
                if (!response.ok) throw new Error('Failed to fetch customers');
                const customers = await response.json();
                
                customersTableBody.innerHTML = ""; 
                
                if (customers.length === 0) {
                    customersTableBody.innerHTML = '<tr><td colspan="5" style="text-align: center;">No customers found.</td></tr>';
                    return;
                }
                
                customers.forEach(cust => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${escapeHTML(cust.name)}</td>
                        <td>${escapeHTML(cust.email)}</td>
                        <td>${escapeHTML(cust.phone || '')}</td>
                        <td>${escapeHTML(cust.company || '')}</td>
                        <td>
                            <button class="btn btn-secondary btn-sm action-btn edit-btn" data-id="${cust.id}">Edit</button>
                            <button class="btn btn-danger btn-sm action-btn delete-btn" data-id="${cust.id}">Delete</button>
                        </td>
                    `;
                    customersTableBody.appendChild(row);
                });

            } catch (err) {
                console.error(err);
                customersTableBody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: red;">Error loading customers.</td></tr>`;
            }
        }

        customerForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            
            const customerData = {
                name: document.getElementById("cust-name").value,
                email: document.getElementById("cust-email").value,
                phone: document.getElementById("cust-phone").value,
                company: document.getElementById("cust-company").value,
            };
            
            const customerId = customerIdField.value;
            let url = '/api/customer';
            let method = 'POST';

            if (customerId) {
                url = `/api/customer/${customerId}`;
                method = 'PUT';
            }

            try {
                const response = await fetch(url, {
                    method: method,
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(customerData)
                });

                if (response.ok) {
                    alert(customerId ? 'Customer updated!' : 'Customer created!');
                    customerForm.reset();
                    closeModal();
                    loadCustomers();
                } else {
                    const errorData = await response.json();
                    alert(`Error: ${errorData.error}`);
                }
            } catch (err) {
                console.error('Form submission error:', err);
                alert('An error occurred. Please try again.');
            }
        });

        customersTableBody.addEventListener('click', async (e) => {
            const target = e.target;
            const customerId = target.getAttribute('data-id');

            if (!customerId) return; 

            if (target.classList.contains('delete-btn')) {
                if (!confirm('Are you sure you want to delete this customer?')) {
                    return;
                }
                
                try {
                    const response = await fetch(`/api/customer/${customerId}`, { method: 'DELETE' });
                    if (response.ok) {
                        alert('Customer deleted.');
                        loadCustomers();
                    } else {
                        const errorData = await response.json();
                        alert(`Error: ${errorData.error}`);
                    }
                } catch (err) {
                    console.error('Delete error:', err);
                    alert('An error occurred.');
                }
            }

            if (target.classList.contains('edit-btn')) {
                try {
                    const response = await fetch(`/api/customer/${customerId}`);
                    if (!response.ok) throw new Error('Customer not found');
                    
                    const customer = await response.json();
                    
                    modalTitle.textContent = "Edit Customer";
                    customerIdField.value = customerId;
                    document.getElementById("cust-name").value = customer.name;
                    document.getElementById("cust-email").value = customer.email;
                    document.getElementById("cust-phone").value = customer.phone || '';
                    document.getElementById("cust-company").value = customer.company || '';
                    
                    modal.style.display = "flex";
                    
                } catch (err) {
                    console.error('Edit error:', err);
                    alert('Could not load customer data.');
                }
            }
        });

        loadCustomers();
    }
    
    // --- 4. DASHBOARD PAGE LOGIC ---
    if (window.location.pathname === '/') {
        const statTotalCustomers = document.getElementById('stat-total-customers');
        if (statTotalCustomers) {
            fetch('/api/customers')
                .then(res => res.json())
                .then(customers => {
                    statTotalCustomers.textContent = customers.length;
                })
                .catch(err => {
                    console.error('Error loading customer stat:', err);
                    statTotalCustomers.textContent = 'N/A';
                });
        }
    }

    // --- 5. LEAD FORM LOGIC (FROM TEAMMATE) ---
    // We'll need to create a new page/modal for this form later
    const leadForm = document.getElementById("lead-form");
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
    // --- END TEAMMATE'S LOGIC ---


    // --- 6. UTILITY FUNCTION ---
    function escapeHTML(str) {
        return str.replace(/[&<>"']/g, function(m) {
            return {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#39;'
            }[m];
        });
    }

});