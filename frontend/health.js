function updateHealth() {
    fetch('/health')
        .then(response => response.json())
        .then(data => {
            const healthDiv = document.getElementById('health-info');
            if (!healthDiv) return;

            const timestamp = new Date(data.timestamp * 1000).toLocaleTimeString();
            
            let html = `
                <div class="health-panel">
                    <h3>System Health (Updated: ${timestamp})</h3>
                    <div class="health-status ${data.status}">
                        Status: ${data.status.toUpperCase()}
                    </div>
                    <div class="metrics">
                        <div class="metric">
                            <label>CPU Usage:</label>
                            <div class="progress-bar">
                                <div class="progress" style="width: ${data.system.cpu_percent}%"></div>
                            </div>
                            <span>${data.system.cpu_percent.toFixed(1)}%</span>
                        </div>
                        <div class="metric">
                            <label>Memory Usage:</label>
                            <div class="progress-bar">
                                <div class="progress" style="width: ${data.system.memory_percent}%"></div>
                            </div>
                            <span>${data.system.memory_percent.toFixed(1)}%</span>
                        </div>
                        <div class="metric">
                            <label>Disk Usage:</label>
                            <div class="progress-bar">
                                <div class="progress" style="width: ${data.system.disk_percent}%"></div>
                            </div>
                            <span>${data.system.disk_percent.toFixed(1)}%</span>
                        </div>
                    </div>
                    <div class="app-info">
                        <p>Frontend Image: ${data.app.frontend_image_exists ? '✅' : '❌'}</p>
                        ${data.app.frontend_image_last_modified ? 
                            `<p>Last Updated: ${new Date(data.app.frontend_image_last_modified * 1000).toLocaleTimeString()}</p>` 
                            : ''}
                    </div>
                </div>
            `;
            
            healthDiv.innerHTML = html;
        })
        .catch(error => {
            console.error('Error fetching health info:', error);
            const healthDiv = document.getElementById('health-info');
            if (healthDiv) {
                healthDiv.innerHTML = '<div class="health-panel error">Error fetching health information</div>';
            }
        });
}

// Update health info every 5 seconds
setInterval(updateHealth, 5000);
// Initial update
updateHealth(); 