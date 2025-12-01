// Track last display state to avoid unnecessary updates
let lastDisplayCount = -1;
let lastDisplayData = null;

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

async function fetchCurrentDisplay() {
    try {
        const result = await apiCall('/api/display/current');

        if (result.success && result.data) {
            const display = result.data;

            // Check what changed
            const displayCountChanged = display.display_count !== lastDisplayCount;
            const metadataChanged = JSON.stringify(display) !== JSON.stringify(lastDisplayData);

            // Only update if something actually changed
            if (!metadataChanged && !displayCountChanged) {
                return; // Nothing changed, skip update entirely
            }

            const container = document.getElementById('current-display-content');
            if (!container) return;

            // Update image ONLY if display count changed
            if (display.has_preview && displayCountChanged) {
                let previewDiv = container.querySelector('.display-preview');

                if (!previewDiv) {
                    // Create preview container if doesn't exist
                    previewDiv = document.createElement('div');
                    previewDiv.className = 'display-preview';
                    container.insertBefore(previewDiv, container.firstChild);
                }

                // Update image with cache buster
                const timestamp = new Date().getTime();
                previewDiv.innerHTML = `
                    <img src="/api/display/preview?t=${timestamp}"
                         alt="Current Display"
                         class="preview-image"
                         onerror="this.style.display='none'; this.nextElementSibling.style.display='block';">
                    <div class="preview-placeholder" style="display:none;">
                        <div class="preview-icon">⚠️</div>
                        <p class="preview-text">Preview not available</p>
                    </div>
                `;

                lastDisplayCount = display.display_count;
            } else if (display.has_preview && !displayCountChanged) {
                // Image hasn't changed - do nothing (no flicker!)
            } else if (!display.has_preview) {
                // First time or no preview available
                let previewDiv = container.querySelector('.display-preview');
                if (!previewDiv || displayCountChanged) {
                    const previewHtml = display.has_preview ? `
                        <div class="display-preview">
                            <img src="/api/display/preview?t=${new Date().getTime()}"
                                 alt="Current Display"
                                 class="preview-image"
                                 onerror="this.style.display='none'; this.nextElementSibling.style.display='block';">
                            <div class="preview-placeholder" style="display:none;">
                                <div class="preview-icon">⚠️</div>
                                <p class="preview-text">Preview not available</p>
                            </div>
                        </div>
                    ` : `
                        <div class="display-preview">
                            <div class="preview-placeholder">
                                <div class="preview-icon">🖼️</div>
                                <p class="preview-text">Physical E-ink Display</p>
                                <p class="preview-note">Enable save_images in driver config for preview</p>
                            </div>
                        </div>
                    `;

                    if (!previewDiv) {
                        container.insertAdjacentHTML('afterbegin', previewHtml);
                    } else {
                        previewDiv.outerHTML = previewHtml;
                    }
                }
            }

            // Update metadata ONLY if it changed
            if (metadataChanged) {
                let metadataDiv = container.querySelector('.display-metadata');

                const metadataHtml = `
                    <div class="metadata-item">
                        <span class="label">Plugin:</span>
                        <span class="value">${display.plugin_name || 'N/A'}</span>
                    </div>
                    <div class="metadata-item">
                        <span class="label">Instance:</span>
                        <span class="value">${display.instance_name || 'N/A'}</span>
                    </div>
                    <div class="metadata-item">
                        <span class="label">Last Updated:</span>
                        <span class="value">${formatTimestamp(display.last_update)}</span>
                    </div>
                    <div class="metadata-item">
                        <span class="label">Status:</span>
                        <span class="value status-${display.status}">${display.status}</span>
                    </div>
                    ${display.display_count ? `
                    <div class="metadata-item">
                        <span class="label">Display Count:</span>
                        <span class="value">${display.display_count}</span>
                    </div>
                    ` : ''}
                `;

                if (!metadataDiv) {
                    const div = document.createElement('div');
                    div.className = 'display-metadata';
                    div.innerHTML = metadataHtml;
                    container.appendChild(div);
                } else {
                    metadataDiv.innerHTML = metadataHtml;
                }
            }

            lastDisplayData = display;
        } else {
            showInfo('current-display-content', 'No image currently displayed');
        }
    } catch (error) {
        showError('current-display-content', `Failed to fetch display: ${error.message}`);
    }
}

async function fetchSourceStats() {
    try {
        const result = await apiCall('/api/source/stats');

        if (result.success) {
            const stats = result.data;
            const statsHtml = `
                <div class="stats-grid">
                    <div class="stat-item">
                        <div class="stat-value">${stats.total_photos || 'N/A'}</div>
                        <div class="stat-label">Total Photos</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${stats.album_name || 'N/A'}</div>
                        <div class="stat-label">Album</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${stats.last_sync || 'Never'}</div>
                        <div class="stat-label">Last Sync</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${stats.provider || 'N/A'}</div>
                        <div class="stat-label">Provider</div>
                    </div>
                </div>
            `;
            setElementContent('source-stats-content', statsHtml);
        } else {
            showError('source-stats-content', result.error);
        }
    } catch (error) {
        showError('source-stats-content', `Failed to fetch stats: ${error.message}`);
    }
}

function refresh() {
    fetchStatus();
    fetchConnections();
    fetchSchedulerStatus();
    fetchCurrentDisplay();
    fetchSourceStats();
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