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
    const dateRangeFilter = document.getElementById('date-range-filter');
    const startDateInput = document.getElementById('start-date');
    const endDateInput = document.getElementById('end-date');
    const customDateRange = document.querySelector('.custom-date-range');
    
    // Set default dates (current three months)
    const today = new Date();
    const threeMonthsAgo = new Date();
    threeMonthsAgo.setMonth(today.getMonth() - 3);
    
    startDateInput.valueAsDate = threeMonthsAgo;
    endDateInput.valueAsDate = today;
    
    // Show/hide custom date inputs based on selection
    dateRangeFilter.addEventListener('change', () => {
        if (dateRangeFilter.value === 'custom') {
            customDateRange.style.display = 'block';
        } else {
            customDateRange.style.display = 'none';
        }
    });
    
    statusFilter.addEventListener('change', updateDashboard);
    faultTypeFilter.addEventListener('change', updateDashboard);
    dateRangeFilter.addEventListener('change', updateDashboard);
    startDateInput.addEventListener('change', updateDashboard);
    endDateInput.addEventListener('change', updateDashboard);

    // Keep track of chart instances
    let monthlyChart = null;
    let categoryChart = null;

    function updateKPIDisplay(kpiData) {
        // Display KPIs with null checks
        document.getElementById('cm-kpi1').textContent = `Total: ${kpiData.total || 0}`;
        document.getElementById('cm-kpi2').textContent = `Closed: ${kpiData.closed_percent || 0}%`;
        document.getElementById('cm-kpi3').textContent = `Remaining: ${kpiData.remaining_percent || 0}%`;
        document.getElementById('cm-kpi4').textContent = `Waiting Parts: ${kpiData.waiting_parts_percent || 0}%`;
        document.getElementById('cm-kpi5').textContent = `New: ${kpiData.new || 0}`;

        // Destroy existing charts if they exist
        if (monthlyChart) monthlyChart.destroy();
        if (categoryChart) categoryChart.destroy();

        // Create monthly closed workorders chart with null checks
        const months = Object.keys(kpiData.monthly_closed || {}).sort();
        const closedCounts = months.map(month => kpiData.monthly_closed[month] || 0);
        
        monthlyChart = new Chart(
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
        categoryChart = new Chart(
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
    }

    async function updateDashboard() {
        try {
            // Initialize empty KPI data structure
            let kpiData = {
                total: 0,
                closed_percent: 0,
                remaining_percent: 0,
                waiting_parts_percent: 0,
                new: 0,
                monthly_closed: {},
                categories: {}
            };

            // Build query params
            const params = new URLSearchParams();
            
            // Add status filter if not 'all'
            if (statusFilter.value !== 'all') {
                params.append('status', statusFilter.value);
            }
            
            // Add fault type filter if not 'all'
            if (faultTypeFilter.value !== 'all') {
                params.append('fault_type', faultTypeFilter.value);
            }
            
            // Handle date range filter
            if (dateRangeFilter.value === '3months') {
                const today = new Date();
                const threeMonthsAgo = new Date();
                threeMonthsAgo.setMonth(today.getMonth() - 3);
                
                params.append('start_date', threeMonthsAgo.toISOString().split('T')[0]);
                params.append('end_date', today.toISOString().split('T')[0]);
            } else if (dateRangeFilter.value === 'custom') {
                if (startDateInput.value && endDateInput.value) {
                    params.append('start_date', startDateInput.value);
                    params.append('end_date', endDateInput.value);
                }
            }
            // 'all' time period - no date filters needed

            // Fetch data via streaming endpoint
            console.log('Fetching streaming data from server...');
            try {
                const response = await fetch(`http://localhost:5000/stream_data?${params.toString()}`);
                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                
                // Process streaming response
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let buffer = '';
                
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    
                    buffer += decoder.decode(value, { stream: true });
                    
                    // Process complete lines
                    const lines = buffer.split('\n');
                    buffer = lines.pop(); // Save incomplete line for next chunk
                    
                    for (const line of lines) {
                        if (!line.trim()) continue;
                        
                        try {
                            const record = JSON.parse(line);
                            
                            // Handle error records
                            if (record.error) {
                                console.error('Stream error:', record);
                                continue;
                            }
                            
                            // Update KPIs incrementally
                            kpiData.total++;
                            if (record.status === 'Completed') {
                                kpiData.closed_percent = ((kpiData.closed_percent || 0) + 1) / kpiData.total * 100;
                            } else if (record.status === 'Wait for Spare Parts') {
                                kpiData.waiting_parts_percent = ((kpiData.waiting_parts_percent || 0) + 1) / kpiData.total * 100;
                            }
                            // Calculate remaining percentage
                            kpiData.remaining_percent = 100 - (kpiData.closed_percent + kpiData.waiting_parts_percent);
                            
                            // Update monthly counts
                            const month = record.month || 'Unknown';
                            kpiData.monthly_closed[month] = (kpiData.monthly_closed[month] || 0) + (record.status === 'Completed' ? 1 : 0);
                            
                            // Update category counts
                            const category = record.Job_type || 'Other';
                            kpiData.categories[category] = (kpiData.categories[category] || 0) + 1;
                            
                            // Update UI periodically (every 10 records)
                            if (kpiData.total % 10 === 0) {
                                updateKPIDisplay(kpiData);
                            }
                        } catch (e) {
                            console.error('Error parsing stream record:', e, line);
                        }
                    }
                }
                
                // Final UI update
                updateKPIDisplay(kpiData);
                
            } catch (error) {
                console.error('Error fetching streaming data:', error);
                const errorElement = document.getElementById('cm-error');
                errorElement.innerHTML = `
                    <p>Failed to connect to server</p>
                    <p>Error: ${error.message}</p>
                    <p>Make sure the server is running at http://localhost:5000</p>
                    <p>Check browser console (F12) for details</p>
                `;
                errorElement.style.color = 'red';
            }
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
    }
});
