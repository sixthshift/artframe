// Track last display state to avoid unnecessary updates
let lastDisplayCount = -1;
let lastDisplayData = null;

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
                                <p class="preview-note">Preview only available with mock driver</p>
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

async function fetchHistory() {
    try {
        const result = await apiCall('/api/display/history');

        if (result.success && result.data && result.data.length > 0) {
            const historyHtml = `
                <div class="history-grid">
                    ${result.data.map(item => `
                        <div class="history-item">
                            <div class="history-thumbnail">
                                <div class="thumbnail-placeholder">📷</div>
                            </div>
                            <div class="history-info">
                                <div class="history-style">${item.style}</div>
                                <div class="history-time">${item.timestamp}</div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
            setElementContent('history-content', historyHtml);
        } else {
            showInfo('history-content', 'No history available');
        }
    } catch (error) {
        showError('history-content', `Failed to fetch history: ${error.message}`);
    }
}

function refresh() {
    fetchCurrentDisplay();
    fetchSourceStats();
    fetchHistory();
}

// Initial load
refresh();

// Poll every 2 seconds (reduced from 1s to minimize flicker)
setInterval(refresh, 2000);