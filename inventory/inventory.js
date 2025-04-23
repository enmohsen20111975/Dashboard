// Inventory Dashboard
document.addEventListener('DOMContentLoaded', async () => {
    try {
        // Fetch data from server
        const response = await fetch('/table_lengths');
        const data = await response.json();

        // Display KPIs
        document.getElementById('inv-kpi1').textContent = `Total Items: ${data.sage || 0}`;
        document.getElementById('inv-kpi2').textContent = `Workorders: ${data.Workorders || 0}`;
        document.getElementById('inv-kpi3').textContent = `Annual Consumption: ${data['Annual Consumption Sep. 2024'] || 0}`;

        // Initialize charts
        const chartData = {
            labels: ['Sage Items', 'Workorders', 'Annual Consumption'],
            datasets: [{
                label: 'Inventory Data',
                data: [data.sage || 0, data.Workorders || 0, data['Annual Consumption Sep. 2024'] || 0],
                backgroundColor: [
                    'rgba(54, 162, 235, 0.2)',
                    'rgba(255, 99, 132, 0.2)',
                    'rgba(255, 206, 86, 0.2)'
                ],
                borderColor: [
                    'rgba(54, 162, 235, 1)',
                    'rgba(255, 99, 132, 1)',
                    'rgba(255, 206, 86, 1)'
                ],
                borderWidth: 1
            }]
        };

        const config = {
            type: 'doughnut',
            data: chartData,
            options: {
                responsive: true,
                plugins: {
                    legend: { position: 'top' },
                    title: { display: true, text: 'Inventory Data Overview' }
                }
            }
        };

        const ctx = document.getElementById('invChart').getContext('2d');
        new Chart(ctx, config);

    } catch (error) {
        console.error('Error loading Inventory dashboard:', error);
        document.getElementById('inv-error').textContent = 'Failed to load dashboard data';
    }
});
