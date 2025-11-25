// Function to fetch data from a given endpoint
async function fetchData(endpoint) {
    const response = await fetch(endpoint);
    if (!response.ok) {
        console.error(`Error fetching data from ${endpoint}:`, response.status);
        return null;
    }
    return response.json();
}

// Function to render all KPIs
async function renderKpiReport() {
    const statsContainer = document.getElementById('kpi-stats-container');
    const reportDateElement = document.getElementById('report-date');
    reportDateElement.textContent = new Date().toLocaleDateString();

    const [salesKpis, customerKpis, ticketMetrics] = await Promise.all([
        fetchData('/api/sales-kpis'),
        fetchData('/api/customer-kpis'),
        fetchData('/api/ticket-metrics')
    ]);

    statsContainer.innerHTML = '';
    
    // Helper to generate the HTML for a stat card
    const createStatCard = (title, value, unit = '') => `
        <div class="card stat-card">
            <h3>${title}</h3>
            <p>${value} ${unit}</p>
        </div>
    `;

    if (salesKpis && customerKpis && ticketMetrics) {
        
        let html = '';
        
        // --- Customer KPIs ---
        html += createStatCard('Total Customers', customerKpis.total_customers);
        html += createStatCard('New Customers (30D)', customerKpis.new_customers_last_30_days);
        
        // --- Sales KPIs ---
        html += createStatCard('Total Opportunities', salesKpis.total_opportunities);
        html += createStatCard('Won Opportunities', salesKpis.won_opportunities);
        html += createStatCard('Open Opportunities', salesKpis.open_opportunities);
        html += createStatCard('Total Revenue Won', `$${salesKpis.total_revenue_won.toFixed(2)}`);

        // --- Ticket KPIs ---
        html += createStatCard('Total Resolved Tickets', ticketMetrics.total_resolved);
        html += createStatCard('Avg. Resolution Time', ticketMetrics.avg_resolution_hours.toFixed(1), 'hrs');
        
        statsContainer.innerHTML = html;

        // Render the chart only if ticket metrics are available
        if (ticketMetrics.avg_resolution_hours >= 0) {
            renderResolutionChart(ticketMetrics.avg_resolution_hours, ticketMetrics.total_resolved);
        }

    } else {
        statsContainer.innerHTML = '<p style="color: red;">Failed to load all KPI data.</p>';
    }
}

// Function to render the Resolution Chart
function renderResolutionChart(avgResolutionHours, totalResolved) {
    const ctx = document.getElementById('report-resolution-chart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Average Time'],
            datasets: [{
                label: 'Avg. Resolution (Hours)',
                data: [avgResolutionHours],
                backgroundColor: '#6c63ff',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: true, title: { display: true, text: 'Hours' } }
            },
            plugins: {
                legend: { display: false },
                title: { display: true, text: `Resolution Performance (Total Resolved: ${totalResolved})` }
            }
        }
    });
}


document.addEventListener('DOMContentLoaded', renderKpiReport);