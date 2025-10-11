async function fetchCurrentDisplay() {
    try {
        const result = await apiCall('/api/display/current');

        if (result.success && result.data) {
            const display = result.data;
            const displayHtml = `
                <div class="display-preview">
                    <div class="preview-placeholder">
                        <div class="preview-icon">🖼️</div>
                        <p class="preview-text">Image Preview</p>
                        <p class="preview-note">E-ink display preview coming soon</p>
                    </div>
                    <div class="display-metadata">
                        <div class="metadata-item">
                            <span class="label">Style:</span>
                            <span class="value">${display.style || 'N/A'}</span>
                        </div>
                        <div class="metadata-item">
                            <span class="label">Last Updated:</span>
                            <span class="value">${formatTimestamp(display.last_update)}</span>
                        </div>
                        <div class="metadata-item">
                            <span class="label">Image ID:</span>
                            <span class="value">${display.image_id || 'None'}</span>
                        </div>
                    </div>
                </div>
            `;
            setElementContent('current-display-content', displayHtml);
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

refresh();
setInterval(refresh, 1000);