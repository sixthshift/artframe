async function fetchStatus() {
    try {
        const result = await apiCall('/api/status');

        if (result.success) {
            const status = result.data;
            const statusHtml = `
                <div class="status-grid">
                    <div class="status-item">
                        <span class="label">Running:</span>
                        <span class="value ${status.running ? 'success' : 'error'}">
                            ${status.running ? '✓ Yes' : '✗ No'}
                        </span>
                    </div>
                    <div class="status-item">
                        <span class="label">Last Update:</span>
                        <span class="value">${status.last_update || 'Never'}</span>
                    </div>
                    <div class="status-item">
                        <span class="label">Next Scheduled:</span>
                        <span class="value">${status.next_scheduled || 'N/A'}</span>
                    </div>
                    <div class="status-item">
                        <span class="label">Cache Images:</span>
                        <span class="value">${status.cache_stats.total_images}</span>
                    </div>
                    <div class="status-item">
                        <span class="label">Cache Size:</span>
                        <span class="value">${status.cache_stats.total_size_mb} MB</span>
                    </div>
                    <div class="status-item">
                        <span class="label">Display Status:</span>
                        <span class="value">${status.display_state.status}</span>
                    </div>
                    <div class="status-item">
                        <span class="label">Display Errors:</span>
                        <span class="value ${status.display_state.error_count > 0 ? 'error' : 'success'}">
                            ${status.display_state.error_count}
                        </span>
                    </div>
                </div>
            `;
            setElementContent('status-content', statusHtml);
        } else {
            showError('status-content', result.error);
        }
    } catch (error) {
        showError('status-content', `Failed to fetch status: ${error.message}`);
    }
}

async function fetchConnections() {
    try {
        const result = await apiCall('/api/connections');

        if (result.success) {
            const connections = result.data;
            let connectionsHtml = '<div class="connections-grid">';

            for (const [service, connected] of Object.entries(connections)) {
                connectionsHtml += `
                    <div class="connection-item">
                        <span class="label">${service.charAt(0).toUpperCase() + service.slice(1)}:</span>
                        <span class="value ${connected ? 'success' : 'error'}">
                            ${connected ? '✓ Connected' : '✗ Failed'}
                        </span>
                    </div>
                `;
            }

            connectionsHtml += '</div>';
            setElementContent('connections-content', connectionsHtml);
        } else {
            showError('connections-content', result.error);
        }
    } catch (error) {
        showError('connections-content', `Failed to fetch connections: ${error.message}`);
    }
}

async function fetchSchedulerStatus() {
    try {
        const result = await apiCall('/api/scheduler/status');

        if (result.success) {
            const status = result.data;
            const toggleBtn = document.getElementById('scheduler-toggle-btn');
            const statusBar = document.getElementById('scheduler-status');

            if (status.paused) {
                toggleBtn.textContent = '▶️ Resume Scheduler';
                toggleBtn.className = 'btn btn-success';
            } else {
                toggleBtn.textContent = '⏸️ Pause Scheduler';
                toggleBtn.className = 'btn btn-warning';
            }

            const nextUpdate = new Date(status.next_update).toLocaleString();
            const pausedIndicator = status.paused ? '<span class="badge badge-warning">PAUSED</span>' : '<span class="badge badge-success">ACTIVE</span>';

            statusBar.innerHTML = `
                <div class="scheduler-info">
                    <span><strong>Scheduler:</strong> ${pausedIndicator}</span>
                    <span><strong>Next Update:</strong> ${nextUpdate}</span>
                    ${status.paused ? '<span class="safety-note">⚡ Daily e-ink refresh still active for screen health</span>' : ''}
                </div>
            `;
        }
    } catch (error) {
        console.error('Failed to fetch scheduler status:', error);
    }
}

async function toggleScheduler() {
    const toggleBtn = document.getElementById('scheduler-toggle-btn');
    const isPaused = toggleBtn.textContent.includes('Resume');

    toggleBtn.disabled = true;

    try {
        const endpoint = isPaused ? '/api/scheduler/resume' : '/api/scheduler/pause';
        const result = await apiCall(endpoint, { method: 'POST' });

        if (result.success) {
            showNotification('✓ ' + result.message, 'success');
            await fetchSchedulerStatus();
        } else {
            showNotification('✗ Failed: ' + result.error, 'error');
        }
    } catch (error) {
        showNotification('✗ Failed: ' + error.message, 'error');
    } finally {
        toggleBtn.disabled = false;
    }
}

function refresh() {
    fetchStatus();
    fetchConnections();
    fetchSchedulerStatus();
}

async function triggerUpdate() {
    const button = event.target;
    button.disabled = true;
    button.textContent = '⏳ Updating...';

    try {
        const result = await apiCall('/api/update', { method: 'POST' });

        if (result.success) {
            showNotification('✓ Update completed successfully', 'success');
            setTimeout(refresh, 1000);
        } else {
            showNotification('✗ Update failed: ' + (result.error || result.message), 'error');
        }
    } catch (error) {
        showNotification('✗ Update failed: ' + error.message, 'error');
    } finally {
        button.disabled = false;
        button.textContent = '🔄 Update Now';
    }
}

async function clearDisplay() {
    if (!confirm('Are you sure you want to clear the display?')) {
        return;
    }

    const button = event.target;
    button.disabled = true;

    try {
        const result = await apiCall('/api/clear', { method: 'POST' });

        if (result.success) {
            showNotification('✓ Display cleared', 'success');
        } else {
            showNotification('✗ Failed to clear display: ' + result.error, 'error');
        }
    } catch (error) {
        showNotification('✗ Failed to clear display: ' + error.message, 'error');
    } finally {
        button.disabled = false;
    }
}

refresh();
setInterval(refresh, 1000);