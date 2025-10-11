async function fetchSystemInfo() {
    try {
        const result = await apiCall('/api/system/info');

        if (result.success) {
            const info = result.data;
            const infoHtml = `
                <div class="info-grid">
                    <div class="info-item">
                        <span class="label">CPU Usage:</span>
                        <span class="value">${info.cpu_percent || 'N/A'}%</span>
                    </div>
                    <div class="info-item">
                        <span class="label">Memory:</span>
                        <span class="value">${info.memory_percent || 'N/A'}%</span>
                    </div>
                    <div class="info-item">
                        <span class="label">Temperature:</span>
                        <span class="value">${info.temperature || 'N/A'}°C</span>
                    </div>
                    <div class="info-item">
                        <span class="label">Disk Usage:</span>
                        <span class="value">${info.disk_percent || 'N/A'}%</span>
                    </div>
                    <div class="info-item">
                        <span class="label">Uptime:</span>
                        <span class="value">${info.uptime || 'N/A'}</span>
                    </div>
                    <div class="info-item">
                        <span class="label">Platform:</span>
                        <span class="value">${info.platform || 'N/A'}</span>
                    </div>
                </div>
            `;
            setElementContent('system-info-content', infoHtml);
        } else {
            showError('system-info-content', result.error);
        }
    } catch (error) {
        showError('system-info-content', `Failed to fetch system info: ${error.message}`);
    }
}

async function fetchEinkHealth() {
    try {
        const result = await apiCall('/api/display/health');

        if (result.success) {
            const health = result.data;
            const healthHtml = `
                <div class="info-grid">
                    <div class="info-item">
                        <span class="label">Total Refreshes:</span>
                        <span class="value">${health.refresh_count || 0}</span>
                    </div>
                    <div class="info-item">
                        <span class="label">Last Refresh:</span>
                        <span class="value">${formatTimestamp(health.last_refresh)}</span>
                    </div>
                    <div class="info-item">
                        <span class="label">Status:</span>
                        <span class="value status-${health.status}">${health.status || 'Unknown'}</span>
                    </div>
                    <div class="info-item">
                        <span class="label">Error Count:</span>
                        <span class="value">${health.error_count || 0}</span>
                    </div>
                </div>
            `;
            setElementContent('eink-health-content', healthHtml);
        } else {
            showError('eink-health-content', result.error);
        }
    } catch (error) {
        showError('eink-health-content', `Failed to fetch e-ink health: ${error.message}`);
    }
}

async function fetchCacheStats() {
    try {
        const result = await apiCall('/api/status');

        if (result.success) {
            const stats = result.data.cache_stats;
            const statsHtml = `
                <div class="info-grid">
                    <div class="info-item">
                        <span class="label">Total Images:</span>
                        <span class="value">${stats.total_images || 0}</span>
                    </div>
                    <div class="info-item">
                        <span class="label">Cache Size:</span>
                        <span class="value">${stats.total_size_mb || 0} MB</span>
                    </div>
                    <div class="info-item">
                        <span class="label">Oldest Image:</span>
                        <span class="value">${stats.oldest_image || 'N/A'}</span>
                    </div>
                    <div class="info-item">
                        <span class="label">Newest Image:</span>
                        <span class="value">${stats.newest_image || 'N/A'}</span>
                    </div>
                </div>
            `;
            setElementContent('cache-stats-content', statsHtml);
        } else {
            showError('cache-stats-content', result.error);
        }
    } catch (error) {
        showError('cache-stats-content', `Failed to fetch cache stats: ${error.message}`);
    }
}

async function fetchLogs() {
    try {
        const level = document.getElementById('log-level-filter').value;
        const result = await apiCall(`/api/system/logs?level=${level}`);

        if (result.success && result.data && result.data.length > 0) {
            const logsHtml = result.data.map(log => `
                <div class="log-entry log-${log.level.toLowerCase()}">
                    <span class="log-time">${log.timestamp}</span>
                    <span class="log-level">${log.level}</span>
                    <span class="log-message">${log.message}</span>
                </div>
            `).join('');
            setElementContent('logs-content', logsHtml);
        } else {
            showInfo('logs-content', 'No logs available');
        }
    } catch (error) {
        showError('logs-content', `Failed to fetch logs: ${error.message}`);
    }
}

async function refreshLogs() {
    await fetchLogs();
}

async function exportLogs() {
    try {
        const response = await fetch('/api/system/logs/export');
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `artframe-logs-${new Date().toISOString()}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    } catch (error) {
        alert('Failed to export logs: ' + error.message);
    }
}

document.getElementById('log-level-filter').addEventListener('change', fetchLogs);

function refresh() {
    fetchSystemInfo();
    fetchEinkHealth();
    fetchCacheStats();
    fetchLogs();
}

refresh();
setInterval(() => {
    fetchSystemInfo();
    fetchEinkHealth();
    fetchCacheStats();
}, 1000);