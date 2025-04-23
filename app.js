
window.AppData = {
    // Storage functions
    getData: async function(filename) {
        try {
            const response = await fetch(`/api/data/${filename}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const text = await response.text();
            return new Promise((resolve, reject) => {
                Papa.parse(text, {
                    header: true,
                    complete: (results) => {
                        resolve(results.data);
                    },
                    error: (error) => {
                        reject(error);
                    }
                });
            });
        } catch (error) {
            console.error('Error fetching data:', error);
            throw error;
        }
    },
    // Common functions
    showNotification: function(message, type) {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        document.body.appendChild(notification);
        setTimeout(() => notification.remove(), 5000);
    }
};

// Fetch and display table lengths
async function fetchTableLengths() {
    try {
        const response = await fetch('/table_lengths');
        const data = await response.json();
        
        document.getElementById('sage-length').textContent = `Sage: ${data.sage || 0}`;
        document.getElementById('po-length').textContent = `PO: ${data.po || 0}`;
        document.getElementById('pr-length').textContent = `PR: ${data.pr || 0}`;
        document.getElementById('workordersLength').textContent = `Workorders: ${data.Workorders || 0}`;
    } catch (error) {
        console.error('Error fetching table lengths:', error);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    // Set default theme to dark
    document.body.className = 'dark-theme';

    // Theme handling
    document.querySelectorAll('.theme-option').forEach(option => {
        option.addEventListener('click', () => {
            document.body.className = `${option.dataset.theme}-theme`;
            AppData.showNotification(`Theme changed to ${option.dataset.theme}`, 'info');
        });
    });
    
    // Button event listeners
    document.getElementById('cmButton').addEventListener('click', loadCM);
    document.getElementById('inventoryButton').addEventListener('click', loadInventory);
    document.getElementById('bdnButton').addEventListener('click', loadBDN);
    document.getElementById('load-data').addEventListener('click', loadCSVData);

    // Upload form handler
    document.getElementById('uploadForm')?.addEventListener('submit', function(e) {
        e.preventDefault();
        const fileInput = document.getElementById('fileInput');
        const file = fileInput.files[0];
        const formData = new FormData();
        formData.append('file', file);

        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            document.getElementById('message').innerText = data.message || data.error;
        })
        .catch(error => {
            console.error('Error:', error);
            document.getElementById('message').innerText = 'An error occurred.';
        });
    });

    // Fetch and display table lengths
    fetchTableLengths();

   
});

function loadInventory() {
    window.location.href = 'inventory/inventory.html';
}

async function loadCM() {
    try {
        const cmButton = document.getElementById('cmButton');
        cmButton.textContent = 'Loading CM Data...';
        cmButton.disabled = true;
        
        // Show loading overlay
        const loadingOverlay = document.createElement('div');
        loadingOverlay.className = 'loading-overlay';
        loadingOverlay.innerHTML = '<div class="loading-spinner"></div><p>Loading CM Data...</p>';
        document.body.appendChild(loadingOverlay);
        
        const response = await fetch('/all_data');
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        
        const { raw_data } = await response.json();
        if (!Array.isArray(raw_data)) {
            throw new Error('Invalid data format - expected array');
        }
        
        // Store data in localStorage before redirect
        localStorage.setItem('cmWorkorders', JSON.stringify(raw_data));
        window.location.href = 'CM/cm.html';
    } catch (error) {
        console.error('CM load error:', error);
        alert(`Failed to load CM data: ${error.message}\n\nPlease try again.`);
        console.debug('Error details:', error.message);
        const cmButton = document.getElementById('cmButton');
        cmButton.textContent = 'CM (Retry)';
        cmButton.disabled = false;
        
        // Remove loading overlay if it exists
        const overlay = document.querySelector('.loading-overlay');
        if (overlay) overlay.remove();
    }
}

function loadBDN() {
    window.location.href = 'BDN/bdn.html';
}

async function sendDataToServer(files) {
    const formData = new FormData();
    for (const file of files) {
        formData.append('files', file);
    }

    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        console.log('Data sent to server:', result);
        AppData.showNotification('Data sent to server successfully', 'success');
    } catch (error) {
        console.error('Error sending data to server:', error);
        AppData.showNotification('Error sending data to server', 'error');
    }
}

async function loadCSVData() {
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.multiple = true;
    fileInput.accept = '.csv';
    fileInput.style.display = 'none';

    fileInput.addEventListener('change', async function(e) {
        const files = Array.from(e.target.files);
        await sendDataToServer(files);
    });

    fileInput.click();
}
