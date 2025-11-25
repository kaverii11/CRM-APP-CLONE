// static/js/script.js
// Clean, merged, safe version of the CRM front-end logic
// Preserves all existing functionality and adds ticket metrics + chart rendering
// Dynamically loads Chart.js only when needed to avoid adding separate files

/* =========================
   Utility helpers & config
   ========================= */

function toggleTheme() {
    const html = document.documentElement;
    html.classList.toggle('dark-mode');
    const theme = html.classList.contains('dark-mode') ? 'dark' : 'light';
    localStorage.setItem("theme", theme);
}

function displayError(endpoint) {
    console.error(`Error fetching data from ${endpoint}`);
    const elements = document.querySelectorAll('.stat-card p');
    elements.forEach(el => {
        if (el.textContent === 'Loading...' || el.textContent === '0') {
            el.textContent = 'Err';
        }
    });
}

function escapeHTML(str = '') {
    return String(str).replace(/[&<>"']/g, function(m) {
        return {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#39;'
        }[m];
    });
}

/* =========================
   Chart loader utility
   ========================= */

function loadChartJsIfNeeded() {
    return new Promise((resolve, reject) => {
        if (window.Chart) return resolve(window.Chart);

        const script = document.createElement('script');
        script.src = "https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js";
        script.defer = true;
        script.onload = () => {
            if (window.Chart) resolve(window.Chart);
            else reject(new Error("Chart loaded but Chart.js unavailable"));
        };
        script.onerror = () => reject(new Error("Failed to load Chart.js"));
        document.head.appendChild(script);
    });
}

/* =========================
   KPI Fetchers (Dashboard)
   ========================= */

async function fetchCustomerKPIs() {
    try {
        const response = await fetch('/api/customer-kpis');
        if (!response.ok) throw new Error('Failed to fetch customer KPIs: ' + response.statusText);
        const data = await response.json();

        const totalCustomersElement = document.getElementById('stat-total-customers');
        if (totalCustomersElement) {
            totalCustomersElement.textContent = data.total_customers ?? 0;
        }

        const newCustomersElement = document.getElementById('stat-new-customers-30d');
        if (newCustomersElement) {
            newCustomersElement.textContent = data.new_customers_last_30_days ?? 0;
        }
    } catch (err) {
        console.error("Error loading Customer KPIs:", err);
        const el = document.getElementById('stat-new-customers-30d');
        if (el) el.textContent = 'Error';
    }
}

// --------------------------
//   NEW: SALES KPIs FETCHER
// --------------------------
async function fetchSalesKPIs() {
    try {
        const response = await fetch('/api/sales-kpis');
        if (!response.ok) throw new Error("Failed to fetch Sales KPIs");

        const data = await response.json();

        const totalOpp = document.getElementById('stat-total-opportunities');
        const openOpp = document.getElementById('stat-open-opportunities');
        const wonOpp = document.getElementById('stat-won-opportunities');
        const revenueOpp = document.getElementById('stat-total-revenue');

        if (totalOpp) totalOpp.textContent = data.total_opportunities ?? 0;
        if (openOpp) openOpp.textContent = data.open_opportunities ?? 0;
        if (wonOpp) wonOpp.textContent = data.won_opportunities ?? 0;
        if (revenueOpp) revenueOpp.textContent =
            `$${Number(data.total_revenue_won ?? 0).toFixed(2)}`;

        await loadChartJsIfNeeded();
        renderSalesChart(data);

    } catch (err) {
        console.error("Sales KPIs Error:", err);
    }
}

  

function renderSalesChart(kpiData) {
    const canvas = document.getElementById("sales-chart");
    if (!canvas) return;

    const ctx = canvas.getContext("2d");

    // Destroy old instance
    if (window.salesChart) {
        window.salesChart.destroy();
    }

    window.salesChart = new Chart(ctx, {
        type: "bar",
        data: {
            labels: ["Total Opp", "Open", "Won"],
            datasets: [{
                label: "Opportunities",
                data: [
                    kpiData.total_opportunities ?? 0,
                    kpiData.open_opportunities ?? 0,
                    kpiData.won_opportunities ?? 0
                ],
                borderWidth: 2,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
        }
    });
}
async function loadOpportunitiesForSalesPage() {
    const container = document.getElementById("opportunities-list");
    if (!container) return;

    container.innerHTML = "Loading opportunities...";

    try {
        const res = await fetch("/api/opportunities");
        const opps = await res.json();

        if (!Array.isArray(opps) || opps.length === 0) {
            container.innerHTML = "No opportunities found.";
            return;
        }

        container.innerHTML = "";

        opps.forEach(o => {
            const div = document.createElement("div");
            div.classList.add("stat-card");
            div.style.marginBottom = "12px";

            div.innerHTML = `
                <h4>${o.name} <span style="color:gray;">(${o.stage})</span></h4>
                <p>Email: ${o.email}</p>
                <p>Amount: $${o.amount ?? 0}</p>
                <p>Source: ${o.source}</p>

                <button class="btn btn-primary btn-sm"
                    onclick="markOpportunityWon('${o.id}')">
                    Mark as Won
                </button>
            `;

            container.appendChild(div);
        });
    } catch (err) {
        container.innerHTML = "Error loading opportunities.";
        console.error(err);
    }
}
async function markOpportunityWon(opportunityId) {
    if (!confirm("Mark this opportunity as WON?")) return;

    try {
        const res = await fetch(`/api/opportunity/${opportunityId}/status`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ stage: "Won" })
        });

        const data = await res.json();

        if (!res.ok) {
            alert("Failed: " + (data.error || "Unknown error"));
            return;
        }

        alert("Opportunity marked as WON!");

        // Refresh Sales KPIs & Chart
        fetchSalesKPIs();
        renderSalesChart();

        // Reload list
        loadOpportunitiesForSalesPage();

    } catch (error) {
        console.error(error);
        alert("Error updating opportunity.");
    }
}



async function fetchLeadKPIs() {
    try {
        const response = await fetch('/api/lead-kpis');
        if (!response.ok) throw new Error('Failed to fetch lead KPIs');

        const data = await response.json();
        const el = document.getElementById('stat-new-leads');
        if (el) el.textContent = data.new_leads_count ?? 0;

    } catch (err) {
        console.error("Error loading Lead KPIs:", err);
        const el = document.getElementById('stat-new-leads');
        if (el) el.textContent = 'Error';
    }
}

async function fetchOpenTickets() {
    try {
        const response = await fetch('/api/tickets');
        if (!response.ok) throw new Error("Failed to fetch tickets");
        const tickets = await response.json();

        const openTickets = tickets.filter(t => t.status === 'Open').length;
        const el = document.getElementById('stat-open-tickets');
        if (el) el.textContent = openTickets;

    } catch (err) {
        console.error("Error loading open tickets:", err);
        const el = document.getElementById('stat-open-tickets');
        if (el) el.textContent = 'Error';
    }
}
/* =========================
   Ticket Metrics & Chart
   ========================= */

let _resolutionChartInstance = null;

function renderResolutionChart(labels, values) {
    const canvas = document.getElementById('resolution-chart');
    if (!canvas) return;

    // If existing Chart.js instance exists, destroy it
    if (window.resolutionChart && typeof window.resolutionChart.destroy === 'function') {
        try { window.resolutionChart.destroy(); } catch (e) { /* ignore */ }
    }

    const ctx = canvas.getContext('2d');

    // Create chart - keep minimal options so it fits inside your CSS card
    window.resolutionChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Avg Resolution (hrs)',
                data: values,
                borderWidth: 3,
                tension: 0.3,
                fill: false,
                pointRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: true, position: 'top' },
                tooltip: { mode: 'index', intersect: false }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

async function fetchTicketMetrics() {
    const avgResolutionElement = document.getElementById('stat-avg-resolution');

    try {
        const response = await fetch('/api/ticket-metrics');
        if (!response.ok) {
            // Try to read JSON error message for better debugging
            let errMsg = `HTTP ${response.status}`;
            try {
                const errJson = await response.json();
                if (errJson && errJson.error) errMsg = errJson.error;
            } catch (_) {}
            throw new Error('Failed to fetch metrics: ' + errMsg);
        }

        const data = await response.json();

        if (avgResolutionElement) {
            avgResolutionElement.textContent = `${data.avg_resolution_hours ?? 0} hrs`;
        }

        // Ensure Chart.js is loaded, then render
        await loadChartJsIfNeeded();
        renderResolutionChart(data.trend_labels || [], data.trend_values || []);

    } catch (err) {
        console.error("Ticket Metrics Error:", err);
        if (avgResolutionElement) avgResolutionElement.textContent = "Error";
        // Destroy existing chart so stale data isn't shown
        if (window.resolutionChart && typeof window.resolutionChart.destroy === 'function') {
            try { window.resolutionChart.destroy(); } catch (_) {}
        }
    }
}

/* =========================
   Customers page
   ========================= */

function initCustomersPage() {
    const addCustomerBtn = document.getElementById("add-customer-btn");
    const modal = document.getElementById("customer-modal");
    const modalCloseBtn = document.getElementById("modal-close-btn");
    const customerForm = document.getElementById("customer-form");
    const customersTableBody = document.getElementById("customers-table-body");
    const modalTitle = document.getElementById("modal-title");
    const customerIdField = document.getElementById("customer-id");

    if (!customerForm || !customersTableBody) return;

    const openModal = () => {
        if (modalTitle) modalTitle.textContent = "Add New Customer";
        customerForm.reset();
        if (customerIdField) customerIdField.value = "";
        if (modal) modal.style.display = "flex";
    };

    const closeModal = () => {
        if (modal) modal.style.display = "none";
    };

    if (addCustomerBtn) addCustomerBtn.addEventListener("click", openModal);
    if (modalCloseBtn) modalCloseBtn.addEventListener("click", closeModal);
    if (modal) {
        modal.addEventListener("click", (e) => {
            if (e.target === modal) closeModal();
        });
    }

    async function loadCustomers() {
        try {
            const response = await fetch('/api/customers');
            if (!response.ok) throw new Error('Failed to fetch customers');
            const customers = await response.json();

            customersTableBody.innerHTML = "";
            if (!Array.isArray(customers) || customers.length === 0) {
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
        const payload = {
            name: document.getElementById("cust-name").value,
            email: document.getElementById("cust-email").value,
            phone: document.getElementById("cust-phone").value,
            company: document.getElementById("cust-company").value
        };

        const customerId = customerIdField ? customerIdField.value : "";
        let url = '/api/customer';
        let method = 'POST';
        if (customerId) {
            url = `/api/customer/${customerId}`;
            method = 'PUT';
        }

        try {
            const resp = await fetch(url, {
                method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (resp.ok) {
                alert(customerId ? 'Customer updated!' : 'Customer created!');
                customerForm.reset();
                closeModal();
                await loadCustomers();
            } else {
                const errorData = await resp.json();
                alert(`Error: ${errorData.error || resp.statusText}`);
            }
        } catch (err) {
            console.error('Form submission error:', err);
            alert('An error occurred. Please try again.');
        }
    });

    customersTableBody.addEventListener('click', async (e) => {
        const target = e.target;
        const customerId = target.getAttribute && target.getAttribute('data-id');
        if (!customerId) return;

        if (target.classList.contains('delete-btn')) {
            if (!confirm('Are you sure you want to delete this customer?')) return;
            try {
                const r = await fetch(`/api/customer/${customerId}`, { method: 'DELETE' });
                if (r.ok) {
                    alert('Customer deleted.');
                    await loadCustomers();
                } else {
                    const err = await r.json();
                    alert(`Error: ${err.error}`);
                }
            } catch (err) {
                console.error('Delete error:', err);
                alert('An error occurred.');
            }
        }

        if (target.classList.contains('edit-btn')) {
            try {
                const r = await fetch(`/api/customer/${customerId}`);
                if (!r.ok) throw new Error('Customer not found');
                const customer = await r.json();
                if (modalTitle) modalTitle.textContent = "Edit Customer";
                if (customerIdField) customerIdField.value = customerId;
                document.getElementById("cust-name").value = customer.name || '';
                document.getElementById("cust-email").value = customer.email || '';
                document.getElementById("cust-phone").value = customer.phone || '';
                document.getElementById("cust-company").value = customer.company || '';
                if (modal) modal.style.display = "flex";
            } catch (err) {
                console.error('Edit error:', err);
                alert('Could not load customer data.');
            }
        }
    });

    // initial load
    loadCustomers();
}

/* =========================
   Tickets page logic
   ========================= */

const loadTickets = async () => {
    const ticketList = document.getElementById('ticket-list');
    if (!ticketList) return;

    ticketList.innerHTML = '<li>Loading tickets...</li>';
    try {
        const r = await fetch('/api/tickets');
        if (!r.ok) throw new Error('Failed to load tickets');
        const tickets = await r.json();

        if (!Array.isArray(tickets) || tickets.length === 0) {
            ticketList.innerHTML = '<li>No recent tickets found.</li>';
            return;
        }

        ticketList.innerHTML = '';
        tickets.forEach(ticket => {
            const item = document.createElement('li');
            const issue = escapeHTML(ticket.issue || 'No issue description');
            const customer = escapeHTML(ticket.customer_id || 'Unknown customer');
            const priority = escapeHTML(ticket.priority || 'Medium');
            const status = (ticket.status || 'Open');

            let actions = '';
            if (status === 'Open') {
                actions = `
                    <button class="btn btn-sm btn-danger" 
                            style="margin-left: 10px; padding: 4px 8px; font-size: 0.75rem; border-radius: 6px;"
                            onclick="closeTicket('${ticket.id}')">
                        Close Ticket
                    </button>`;
            } else if (status === 'Closed' || status === 'Resolved') {
                actions = '<span style="color: #4CAF50; font-weight: 600; margin-left: 10px;">✓ Resolved</span>';
            } else if (status === 'Escalated') {
                actions = '<span style="color: #FF5722; font-weight: 600; margin-left: 10px;">⚠ Escalated</span>';
            }

            item.innerHTML = `
                <strong>${issue}</strong> 
                — Customer: ${customer} • Priority: ${priority} • Status: ${escapeHTML(status)}
                ${actions}`;
            ticketList.appendChild(item);
        });
    } catch (err) {
        console.error('Failed to load tickets:', err);
        ticketList.innerHTML = '<li style="color: var(--danger-color); font-weight: 500;">Error loading tickets. Please check database connection.</li>';
    }
};

async function closeTicket(ticketId) {
    if (!confirm(`Are you sure you want to CLOSE ticket ${ticketId}? This action cannot be undone.`)) {
        return;
    }

    try {
        const response = await fetch(`/api/ticket/${ticketId}/close`, { method: 'PUT' });
        const result = await response.json();

        if (response.ok && result.success) {
            alert(result.message);
            await loadTickets();
            // Update metrics after closing
            await fetchTicketMetrics();
        } else {
            alert(`Failed to close ticket: ${result.error || response.statusText}`);
        }
    } catch (error) {
        console.error('Error closing ticket:', error);
        alert('An error occurred while closing the ticket.');
    }
}

function initTicketsPage() {
    const ticketForm = document.getElementById('ticket-form');
    const customerSelect = document.getElementById('ticket-customer-select');
    const issueInput = document.getElementById('ticket-issue');
    const prioritySelect = document.getElementById('ticket-priority');
    const ticketStatus = document.getElementById('ticket-status');

    // Guard: if ticket list not present, don't init
    const ticketList = document.getElementById('ticket-list');
    if (!ticketList) return;

    const setTicketStatus = (message, isError = false) => {
        if (!ticketStatus) return;
        ticketStatus.innerHTML = '';
        const span = document.createElement('span');
        span.textContent = message;
        span.style.color = isError ? 'red' : 'inherit';
        ticketStatus.appendChild(span);
    };

    const populateCustomers = async () => {
        if (!customerSelect) return;
        customerSelect.innerHTML = '<option value="">Loading customers...</option>';
        try {
            const r = await fetch('/api/customers');
            if (!r.ok) throw new Error('Failed to load customers');
            const customers = await r.json();
            if (!Array.isArray(customers) || customers.length === 0) {
                customerSelect.innerHTML = '<option value="">No customers found</option>';
                return;
            }
            customerSelect.innerHTML = '<option value="">Select a customer</option>';
            customers.forEach(customer => {
                const option = document.createElement('option');
                option.value = customer.id;
                option.textContent = customer.name || 'Unnamed';
                customerSelect.appendChild(option);
            });
        } catch (err) {
            console.error('Failed to populate customers:', err);
            customerSelect.innerHTML = '<option value="">Error loading customers</option>';
        }
    };

    if (ticketForm) {
        ticketForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const customerId = customerSelect ? customerSelect.value : '';
            const issue = issueInput ? issueInput.value.trim() : '';
            const priority = prioritySelect ? prioritySelect.value : 'Medium';

            if (!customerId) {
                setTicketStatus('Please select a customer.', true);
                return;
            }
            if (!issue) {
                setTicketStatus('Issue description is required.', true);
                return;
            }

            setTicketStatus('Creating ticket...');
            try {
                const resp = await fetch('/api/tickets', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ customer_id: customerId, issue, priority })
                });
                const data = await resp.json();
                if (!resp.ok) throw new Error(data.error || 'Failed to create ticket');
                setTicketStatus(`Ticket created! ID: ${data.ticket_id}`);
                ticketForm.reset();
                if (prioritySelect) prioritySelect.value = 'Medium';
                await loadTickets();
                // update metrics after creating
                await fetchTicketMetrics();
            } catch (err) {
                console.error('Error creating ticket:', err);
                setTicketStatus(`Error creating ticket: ${err.message}`, true);
            }
        });
    }

    // initial load
    populateCustomers();
    loadTickets();
}

/* =========================
   Leads & Loyalty handlers
   ========================= */

function initLeadsAndLoyalty() {
    const leadForm = document.getElementById("lead-form");
    if (leadForm) {
        leadForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const leadData = {
                name: document.getElementById("lead-name").value,
                email: document.getElementById("lead-email").value,
                source: document.getElementById("lead-source").value,
                status: "New"
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

    const loyaltyProfileForm = document.getElementById('loyalty-profile-form');
    const loyaltyOutput = document.getElementById('loyalty-output');

    const showLoyaltyResult = (message, isError = false) => {
        if (!loyaltyOutput) return;
        loyaltyOutput.innerHTML = `<pre${isError ? ' class="error"' : ''}>${message}</pre>`;
    };

    if (loyaltyProfileForm) {
        loyaltyProfileForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const customerId = document.getElementById('loyalty-profile-customer').value.trim();
            if (!customerId) return;
            try {
                const resp = await fetch(`/api/loyalty/${encodeURIComponent(customerId)}`);
                if (!resp.ok) {
                    const errorData = await resp.json();
                    throw new Error(errorData.error || 'Failed to fetch profile');
                }
                const data = await resp.json();
                showLoyaltyResult(JSON.stringify(data, null, 2));
            } catch (err) {
                console.error('Loyalty profile fetch failed:', err);
                showLoyaltyResult(err.message, true);
            }
        });
    }

    const loyaltyPurchaseForm = document.getElementById('loyalty-purchase-form');
    if (loyaltyPurchaseForm) {
        loyaltyPurchaseForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const customerId = document.getElementById('purchase-customer').value.trim();
            const amountValue = document.getElementById('purchase-amount').value;
            if (!customerId || !amountValue) return;
            try {
                const response = await fetch('/api/simulate-purchase', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ customer_id: customerId, amount: amountValue })
                });
                const data = await response.json();
                if (!response.ok) throw new Error(data.error || 'Failed to simulate purchase');
                showLoyaltyResult(JSON.stringify(data, null, 2));
            } catch (err) {
                console.error('Simulate purchase failed:', err);
                showLoyaltyResult(err.message, true);
            }
        });
    }

    const loyaltyRedeemForm = document.getElementById('loyalty-redeem-form');
    if (loyaltyRedeemForm) {
        loyaltyRedeemForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const customerId = document.getElementById('redeem-customer').value.trim();
            const points = document.getElementById('redeem-points').value;
            if (!customerId || !points) return;
            try {
                const response = await fetch(`/api/loyalty/${encodeURIComponent(customerId)}/redeem`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ points_to_redeem: Number(points) })
                });
                const data = await response.json();
                if (!response.ok) throw new Error(data.error || 'Failed to redeem points');
                showLoyaltyResult(JSON.stringify(data, null, 2));
            } catch (err) {
                console.error('Redeem points failed:', err);
                showLoyaltyResult(err.message, true);
            }
        });
    }

    const loyaltyReferralForm = document.getElementById('loyalty-referral-form');
    if (loyaltyReferralForm) {
        loyaltyReferralForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const customerId = document.getElementById('referral-customer').value.trim();
            const referralCode = document.getElementById('referral-code').value.trim();
            if (!customerId || !referralCode) return;
            try {
                const response = await fetch(`/api/loyalty/${encodeURIComponent(customerId)}/use-referral`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ referral_code: referralCode })
                });
                const data = await response.json();
                if (!response.ok) throw new Error(data.error || 'Failed to apply referral');
                showLoyaltyResult(JSON.stringify(data, null, 2));
            } catch (err) {
                console.error('Apply referral failed:', err);
                showLoyaltyResult(err.message, true);
            }
        });
    }
}
let currentLeadId = null;

function openAssignLeadModal(leadId) {
    currentLeadId = leadId;
    document.getElementById("assign-lead-modal").style.display = "flex";
}

function closeAssignLeadModal() {
    document.getElementById("assign-lead-modal").style.display = "none";
}

document.getElementById("close-assign-modal")?.addEventListener("click", () => {
    closeAssignLeadModal();
});
const assignLeadForm = document.getElementById("assign-lead-form");

if (assignLeadForm) {
    assignLeadForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        const repId = document.getElementById("rep-id").value.trim();
        const repName = document.getElementById("rep-name").value.trim();

        if (!repId) {
            alert("Sales Rep ID is required");
            return;
        }

        const response = await fetch(`/api/lead/${currentLeadId}/assign`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                rep_id: repId,
                rep_name: repName
            })
        });

        const data = await response.json();

        if (response.ok) {
            alert("Lead assigned successfully!");
            closeAssignLeadModal();

            // reload leads list if needed
        } else {
            alert("Error: " + (data.error || "Failed"));
        }
    });
}

// script.js (Add Payment Logic)

function initPaymentLogic() {
    const paymentForm = document.getElementById('payment-form');
    const paymentOutput = document.getElementById('payment-output');
    const payMethodSelect = document.getElementById('pay-method');
    const cardGroup = document.getElementById('card-group');
    
    if (!paymentForm) return; // Only run if the form exists

    // Helper to display results
    const showPaymentResult = (message, isError = false) => {
        paymentOutput.innerHTML = `<pre${isError ? ' class="error"' : ''}>${message}</pre>`;
    };
    
    // Toggle Card Number field visibility
    payMethodSelect.addEventListener('change', (e) => {
        if (e.target.value === 'Card') {
            cardGroup.style.display = 'block';
        } else {
            cardGroup.style.display = 'none';
        }
    });

    // Handle form submission
    paymentForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const method = payMethodSelect.value;
        const payload = {
            customer_id: document.getElementById('pay-customer').value.trim(),
            amount: document.getElementById('pay-amount').value,
            method: method,
            card_number: (method === 'Card') ? document.getElementById('pay-card').value.trim() : null
        };

        try {
            const response = await fetch('/api/payment/process', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            
            const data = await response.json();
            
            if (response.ok && data.success) {
                showPaymentResult(JSON.stringify(data, null, 2), false);
            } else {
                // Handle 400 failure status from mock gateway
                const errorMessage = data.error || data.message || 'Payment failed due to an unknown error.';
                showPaymentResult(`STATUS: Failed\nError: ${errorMessage}\nTXN ID: ${data.transaction_id || 'N/A'}`, true);
            }
        } catch (err) {
            console.error('Payment processing failed:', err);
            showPaymentResult(`SYSTEM ERROR: Could not reach payment server.`, true);
        }
    });
}

// Ensure initPaymentLogic is called on DOM load:
// Find your main DOMContentLoaded handler and add the call:
/*
document.addEventListener("DOMContentLoaded", async () => {
    // ... existing setup ...
    
    // Page-specific initializers
    // ...
    
    // Always initialize payment logic if forms are present
    initPaymentLogic(); // <--- ADD THIS LINE
    
    // ... rest of the code
});
*/
/* =========================
   Main initialization
   ========================= */

document.addEventListener("DOMContentLoaded", async () => {
    const themeToggle = document.getElementById("theme-toggle");
    const storedTheme = localStorage.getItem("theme");
    if (storedTheme === "dark") {
        document.documentElement.classList.add("dark-mode");
    }

    if (themeToggle) {
        themeToggle.addEventListener("click", () => {
            toggleTheme();
        });
    }

    const mobileMenuBtn = document.getElementById("mobile-menu-btn");
    if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener("click", () => {
            document.body.classList.toggle("sidebar-open");
        });
    }

    const path = window.location.pathname;

    // Dashboard root
    if (path === "/") {
        // Run KPI fetchers in parallel (non-blocking)
        fetchCustomerKPIs();
        fetchOpenTickets();
        fetchLeadKPIs();
        // ticket metrics (chart)
        try {
            await loadChartJsIfNeeded();
            await fetchTicketMetrics();
        } catch (err) {
            console.warn("Ticket metrics failed:", err);
        }
    }

    // Customers page
    if (path === "/customers") {
        initCustomersPage();
    }

    // Tickets page
    if (path === "/tickets") {
        initTicketsPage();

        // Ensure Chart.js loaded and then fetch ticket metrics
        try {
            await loadChartJsIfNeeded();
            await fetchTicketMetrics();
        } catch (err) {
            console.warn("Failed to initialize charts on tickets page:", err);
        }
    }

    // Sales page
    if (path === "/sales") {
    fetchSalesKPIs();
    renderSalesChart();
    loadOpportunitiesForSalesPage();
}


    // Always initialize leads & loyalty handlers if their forms are present
    initLeadsAndLoyalty();
});

