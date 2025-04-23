// CM Dashboard
document.addEventListener('DOMContentLoaded', async () => {
    // Initialize drawer functionality
    const drawer = document.querySelector('.filter-drawer');
    const openBtn = document.querySelector('.open-drawer');
    const closeBtn = document.querySelector('.close-drawer');
    
    openBtn.addEventListener('click', () => {
        drawer.classList.add('open');
    });
    
    closeBtn.addEventListener('click', () => {
        drawer.classList.remove('open');
    });

    // Initialize dashboard
    const statusFilter = document.getElementById('status-filter');
    const faultTypeFilter = document.getElementById('fault-type-filter');
    
    statusFilter.addEventListener('change', updateDashboard);
    faultTypeFilter.addEventListener('change', updateDashboard);

    try {
        // Fetch pre-calculated KPIs from server with error handling
        console.log('Fetching KPI data from server...');
        let kpiData = {
            total: 0,
            closed_percent: 0,
            remaining_percent: 0,
            waiting_parts_percent: 0,
            new: 0,
            monthly_closed: {},
            categories: {}
        };

        try {
            // Get current filter values
            const statusFilterValue = statusFilter.value === 'all' ? null : statusFilter.value;
            const faultTypeFilterValue = faultTypeFilter.value === 'all' ? null : faultTypeFilter.value;
            
            // Build query parameters
            const params = new URLSearchParams();
            if (statusFilterValue) params.append('status', statusFilterValue);
            if (faultTypeFilterValue) params.append('faultType', faultTypeFilterValue);
            
            const response = await fetch(`/kpi_data?${params.toString()}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            if (data) {
                kpiData = {
                    ...kpiData,
                    ...data
                };
            }
            console.log('Received KPI data:', kpiData);
        } catch (error) {
            console.error('Error fetching KPI data:', error);
        }

        // Display KPIs with null checks
        document.getElementById('cm-kpi1').textContent = `Total: ${kpiData.total || 0}`;
        document.getElementById('cm-kpi2').textContent = `Closed: ${kpiData.closed_percent || 0}%`;
        document.getElementById('cm-kpi3').textContent = `Remaining: ${kpiData.remaining_percent || 0}%`;
        document.getElementById('cm-kpi4').textContent = `Waiting Parts: ${kpiData.waiting_parts_percent || 0}%`;
        document.getElementById('cm-kpi5').textContent = `New: ${kpiData.new || 0}`;

        // Create monthly closed workorders chart with null checks
        const months = Object.keys(kpiData.monthly_closed || {}).sort();
        const closedCounts = months.map(month => kpiData.monthly_closed[month] || 0);
        
        new Chart(
            document.getElementById('monthlyChart').getContext('2d'),
            {
                type: 'bar',
                data: {
                    labels: months,
                    datasets: [{
                        label: 'Closed Workorders',
                        data: closedCounts,
                        backgroundColor: 'rgba(54, 162, 235, 0.5)',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { display: false },
                        title: { display: true, text: 'Closed Workorders by Month' }
                    },
                    scales: {
                        y: { beginAtZero: true }
                    }
                }
            }
        );

        // Create workorders by category chart
        new Chart(
            document.getElementById('categoryChart').getContext('2d'),
            {
                type: 'doughnut',
                data: {
                    labels: Object.keys(kpiData.categories),
                    datasets: [{
                        label: 'Workorders',
                        data: Object.values(kpiData.categories),
                        backgroundColor: [
                            'rgba(255, 99, 132, 0.5)',
                            'rgba(54, 162, 235, 0.5)',
                            'rgba(255, 206, 86, 0.5)',
                            'rgba(75, 192, 192, 0.5)',
                            'rgba(153, 102, 255, 0.5)'
                        ],
                        borderColor: [
                            'rgba(255, 99, 132, 1)',
                            'rgba(54, 162, 235, 1)',
                            'rgba(255, 206, 86, 1)',
                            'rgba(75, 192, 192, 1)',
                            'rgba(153, 102, 255, 1)'
                        ],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { position: 'right' },
                        title: { display: true, text: 'Workorders by Category' }
                    }
                }
            }
        );


    } catch (error) {
        console.error('Error loading CM dashboard:', error);
        const errorElement = document.getElementById('cm-error');
        errorElement.innerHTML = `
            <p>Failed to load dashboard data</p>
            <p>Error: ${error.message}</p>
            <p>Check browser console (F12) for details</p>
            <p>Make sure the server is running and accessible</p>
        `;
        errorElement.style.color = 'red';
    }
});
