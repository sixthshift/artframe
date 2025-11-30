/**
 * Configuration page JavaScript
 * Handles system-level configuration only
 */

let currentConfig = null;

async function fetchConfig() {
    try {
        const result = await apiCall('/api/config');

        if (result.success) {
            currentConfig = result.data;
            renderConfigForm(currentConfig);
        } else {
            showError('config-content', result.error);
        }
    } catch (error) {
        showError('config-content', `Failed to fetch config: ${error.message}`);
    }
}

function renderConfigForm(config) {
    const artframe = config.artframe || {};
    const scheduler = artframe.scheduler || {};
    const display = artframe.display || {};
    const cache = artframe.cache || {};
    const logging = artframe.logging || {};
    const web = artframe.web || {};

    const formHtml = `
        <form id="config-form" class="config-form">
            <!-- Scheduler Section -->
            <div class="config-section">
                <h3>⏰ Scheduler</h3>
                <div class="form-grid">
                    <div class="form-group">
                        <label for="scheduler-timezone">Timezone</label>
                        <input type="text" id="scheduler-timezone" value="${scheduler.timezone || 'America/New_York'}" required>
                        <span class="help-text">e.g., America/New_York, Europe/London, Asia/Tokyo</span>
                    </div>
                    <div class="form-group">
                        <label for="scheduler-default-duration">Default Duration (seconds)</label>
                        <input type="number" id="scheduler-default-duration" value="${scheduler.default_duration || 3600}" min="1" required>
                        <span class="help-text">Default time to display each playlist item</span>
                    </div>
                    <div class="form-group">
                        <label for="scheduler-refresh-interval">Refresh Interval (seconds)</label>
                        <input type="number" id="scheduler-refresh-interval" value="${scheduler.refresh_interval || 86400}" min="1" required>
                        <span class="help-text">Daily refresh for e-ink display health (86400 = 24 hours)</span>
                    </div>
                </div>
            </div>

            <!-- Display Section -->
            <div class="config-section">
                <h3>📺 Display Hardware</h3>
                <div class="form-grid">
                    <div class="form-group">
                        <label for="display-driver">Driver</label>
                        <select id="display-driver" required>
                            <option value="spectra6" ${display.driver === 'spectra6' ? 'selected' : ''}>Spectra 6 E-ink</option>
                            <option value="mock" ${display.driver === 'mock' ? 'selected' : ''}>Mock (Testing)</option>
                        </select>
                        <span class="help-text">E-ink display driver</span>
                    </div>
                    <div class="form-group">
                        <label for="display-width">Width (pixels)</label>
                        <input type="number" id="display-width" value="${display.width || 600}" min="1" required onchange="updateDisplayInfo()">
                        <span class="help-text">Display width in pixels</span>
                    </div>
                    <div class="form-group">
                        <label for="display-height">Height (pixels)</label>
                        <input type="number" id="display-height" value="${display.height || 448}" min="1" required onchange="updateDisplayInfo()">
                        <span class="help-text">Display height in pixels</span>
                    </div>
                    <div class="form-group">
                        <label for="display-rotation">Rotation</label>
                        <select id="display-rotation" required onchange="updateDisplayInfo()">
                            <option value="0" ${display.rotation === 0 ? 'selected' : ''}>0°</option>
                            <option value="90" ${display.rotation === 90 ? 'selected' : ''}>90°</option>
                            <option value="180" ${display.rotation === 180 ? 'selected' : ''}>180°</option>
                            <option value="270" ${display.rotation === 270 ? 'selected' : ''}>270°</option>
                        </select>
                        <span class="help-text">Display orientation</span>
                    </div>
                    <div class="form-group">
                        <label>Display Info</label>
                        <div id="display-info" class="display-info-box"></div>
                    </div>
                </div>
            </div>

            <!-- Storage/Cache Section -->
            <div class="config-section">
                <h3>💾 Storage & Cache</h3>
                <div class="form-grid">
                    <div class="form-group">
                        <label for="cache-directory">Cache Directory</label>
                        <input type="text" id="cache-directory" value="${cache.cache_directory || '~/.artframe/cache'}" required>
                        <span class="help-text">Path to content cache directory (~ expands to home directory)</span>
                    </div>
                    <div class="form-group">
                        <label for="cache-max-size">Max Size (MB)</label>
                        <input type="number" id="cache-max-size" value="${cache.max_size_mb || 500}" min="1" required>
                        <span class="help-text">Maximum cache size in megabytes</span>
                    </div>
                    <div class="form-group">
                        <label for="cache-retention">Retention (days)</label>
                        <input type="number" id="cache-retention" value="${cache.retention_days || 30}" min="1" required>
                        <span class="help-text">Days to keep cached content</span>
                    </div>
                </div>
            </div>

            <!-- Logging Section -->
            <div class="config-section">
                <h3>📊 Logging</h3>
                <div class="form-grid">
                    <div class="form-group">
                        <label for="logging-level">Log Level</label>
                        <select id="logging-level" required>
                            <option value="DEBUG" ${logging.level === 'DEBUG' ? 'selected' : ''}>DEBUG</option>
                            <option value="INFO" ${logging.level === 'INFO' ? 'selected' : ''}>INFO</option>
                            <option value="WARNING" ${logging.level === 'WARNING' ? 'selected' : ''}>WARNING</option>
                            <option value="ERROR" ${logging.level === 'ERROR' ? 'selected' : ''}>ERROR</option>
                        </select>
                        <span class="help-text">Minimum log level to capture</span>
                    </div>
                    <div class="form-group">
                        <label for="logging-file">Log File</label>
                        <input type="text" id="logging-file" value="${logging.file || '~/.artframe/logs/artframe.log'}" required>
                        <span class="help-text">Path to log file (~ expands to home directory)</span>
                    </div>
                    <div class="form-group">
                        <label for="logging-max-size">Max Size (MB)</label>
                        <input type="number" id="logging-max-size" value="${logging.max_size_mb || 10}" min="1" required>
                        <span class="help-text">Maximum log file size before rotation</span>
                    </div>
                    <div class="form-group">
                        <label for="logging-backup-count">Backup Count</label>
                        <input type="number" id="logging-backup-count" value="${logging.backup_count || 5}" min="0" required>
                        <span class="help-text">Number of rotated log files to keep</span>
                    </div>
                </div>
            </div>

            <!-- Web Server Section -->
            <div class="config-section">
                <h3>🌐 Web Server</h3>
                <div class="form-grid">
                    <div class="form-group">
                        <label for="web-host">Host</label>
                        <input type="text" id="web-host" value="${web.host || '0.0.0.0'}" required>
                        <span class="help-text">Web server host (0.0.0.0 = all interfaces, 127.0.0.1 = localhost only)</span>
                    </div>
                    <div class="form-group">
                        <label for="web-port">Port</label>
                        <input type="number" id="web-port" value="${web.port || 8000}" min="1" max="65535" required>
                        <span class="help-text">Web server port</span>
                    </div>
                    <div class="form-group">
                        <label for="web-debug">Debug Mode</label>
                        <input type="checkbox" id="web-debug" ${web.debug ? 'checked' : ''}>
                        <span class="help-text">Enable Flask debug mode (development only)</span>
                    </div>
                </div>
            </div>
        </form>
    `;

    setElementContent('config-content', formHtml);
    updateDisplayInfo();
}

function updateDisplayInfo() {
    const width = parseInt(document.getElementById('display-width')?.value || 600);
    const height = parseInt(document.getElementById('display-height')?.value || 448);
    const rotation = parseInt(document.getElementById('display-rotation')?.value || 0);

    let effectiveWidth = width;
    let effectiveHeight = height;

    // Apply rotation
    if (rotation === 90 || rotation === 270) {
        effectiveWidth = height;
        effectiveHeight = width;
    }

    const orientation = effectiveWidth > effectiveHeight ? 'Landscape' : 'Portrait';
    const aspectRatio = (effectiveWidth / effectiveHeight).toFixed(2);

    const infoBox = document.getElementById('display-info');
    if (infoBox) {
        infoBox.innerHTML = `
            <div class="info-detail">Effective: ${effectiveWidth} × ${effectiveHeight}</div>
            <div class="info-detail">Orientation: <strong>${orientation}</strong></div>
            <div class="info-detail">Aspect Ratio: <strong>${aspectRatio}:1</strong></div>
        `;
    }
}

function getFormValues() {
    return {
        artframe: {
            scheduler: {
                timezone: document.getElementById('scheduler-timezone').value,
                default_duration: parseInt(document.getElementById('scheduler-default-duration').value),
                refresh_interval: parseInt(document.getElementById('scheduler-refresh-interval').value)
            },
            display: {
                driver: document.getElementById('display-driver').value,
                width: parseInt(document.getElementById('display-width').value),
                height: parseInt(document.getElementById('display-height').value),
                rotation: parseInt(document.getElementById('display-rotation').value)
            },
            cache: {
                cache_directory: document.getElementById('cache-directory').value,
                max_size_mb: parseInt(document.getElementById('cache-max-size').value),
                retention_days: parseInt(document.getElementById('cache-retention').value)
            },
            logging: {
                level: document.getElementById('logging-level').value,
                file: document.getElementById('logging-file').value,
                max_size_mb: parseInt(document.getElementById('logging-max-size').value),
                backup_count: parseInt(document.getElementById('logging-backup-count').value)
            },
            web: {
                host: document.getElementById('web-host').value,
                port: parseInt(document.getElementById('web-port').value),
                debug: document.getElementById('web-debug').checked
            }
        }
    };
}

async function saveConfig() {
    const saveBtn = document.getElementById('save-btn');
    const form = document.getElementById('config-form');

    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }

    try {
        const newConfig = getFormValues();

        saveBtn.disabled = true;
        saveBtn.textContent = '💾 Saving...';

        // Validate configuration
        const validateResult = await apiCall('/api/config', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(newConfig)
        });

        if (!validateResult.success) {
            showNotification('✗ Invalid config: ' + validateResult.error, 'error');
            return;
        }

        // Save to file
        const saveResult = await apiCall('/api/config/save', { method: 'POST' });

        if (saveResult.success) {
            showNotification('✓ Configuration saved!', 'success');
            if (saveResult.restart_required) {
                document.getElementById('restart-btn').style.display = 'inline-block';
                showNotification('⚠️ Restart required for changes to take effect', 'warning');
            }
            currentConfig = newConfig;
        } else {
            showNotification('✗ Failed to save: ' + saveResult.error, 'error');
        }
    } catch (e) {
        showNotification('✗ Save failed: ' + e.message, 'error');
    } finally {
        saveBtn.disabled = false;
        saveBtn.textContent = '💾 Save';
    }
}

async function revertConfig() {
    if (!confirm('Revert to saved configuration? Unsaved changes will be lost.')) {
        return;
    }

    const revertBtn = document.getElementById('revert-btn');
    revertBtn.disabled = true;

    try {
        const result = await apiCall('/api/config/revert', { method: 'POST' });

        if (result.success) {
            showNotification('✓ Configuration reverted', 'success');
            await fetchConfig();
            document.getElementById('restart-btn').style.display = 'none';
        } else {
            showNotification('✗ Revert failed: ' + result.error, 'error');
        }
    } catch (error) {
        showNotification('✗ Revert failed: ' + error.message, 'error');
    } finally {
        revertBtn.disabled = false;
    }
}

async function restartApp() {
    if (!confirm('Restart Artframe? This will interrupt any running operations.')) {
        return;
    }

    const restartBtn = document.getElementById('restart-btn');
    restartBtn.disabled = true;
    restartBtn.textContent = '🔄 Restarting...';

    // Fire restart request - don't await since server will die
    fetch('/api/restart', { method: 'POST' }).catch(() => {});

    // Show restarting message
    showNotification('🔄 Restarting server...', 'info');

    // Poll until server is back up
    const maxAttempts = 30;  // 30 seconds max
    let attempts = 0;

    const pollServer = async () => {
        attempts++;
        try {
            const response = await fetch('/api/status', {
                method: 'GET',
                cache: 'no-store'
            });
            if (response.ok) {
                showNotification('✓ Server restarted successfully!', 'success');
                setTimeout(() => window.location.reload(), 1000);
                return;
            }
        } catch (e) {
            // Server still down, keep polling
        }

        if (attempts < maxAttempts) {
            setTimeout(pollServer, 1000);
        } else {
            showNotification('⚠️ Server taking longer than expected. Please refresh manually.', 'warning');
            restartBtn.disabled = false;
            restartBtn.textContent = '🔄 Restart';
        }
    };

    // Start polling after a short delay to let server shut down
    setTimeout(pollServer, 2000);
}

// Initialize
fetchConfig();
