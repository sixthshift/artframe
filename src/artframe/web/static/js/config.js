let currentConfig = null;
let styleCounter = 0;

function renderStylesEditor(styles) {
    if (!styles || styles.length === 0) {
        return '<div class="no-styles">No styles defined. Click "Add Style" to create one.</div>';
    }

    return styles.map((style, index) => {
        // Handle both old format (string) and new format (object)
        const styleName = typeof style === 'string' ? style : style.name;
        const stylePrompt = typeof style === 'string' ? '' : style.prompt;

        return `
            <div class="style-item" data-index="${index}">
                <div class="style-header">
                    <input type="text"
                           class="style-name"
                           id="style-name-${index}"
                           placeholder="Style name (e.g., watercolor)"
                           value="${styleName || ''}"
                           required>
                    <button type="button" class="btn-remove" onclick="removeStyle(${index})">❌</button>
                </div>
                <textarea
                    class="style-prompt"
                    id="style-prompt-${index}"
                    placeholder="Enter the full prompt for this style (e.g., Transform this image into a watercolor painting with soft edges...)"
                    rows="3"
                    required>${stylePrompt || ''}</textarea>
            </div>
        `;
    }).join('');
}

function addStyle() {
    const stylesEditor = document.getElementById('styles-editor');
    const currentStyles = collectStyles();
    currentStyles.push({ name: '', prompt: '' });
    stylesEditor.innerHTML = renderStylesEditor(currentStyles);
}

function removeStyle(index) {
    const stylesEditor = document.getElementById('styles-editor');
    const currentStyles = collectStyles();
    currentStyles.splice(index, 1);
    stylesEditor.innerHTML = renderStylesEditor(currentStyles);
}

function collectStyles() {
    const styleElements = document.querySelectorAll('.style-item');
    const styles = [];

    styleElements.forEach((element, index) => {
        const name = document.getElementById(`style-name-${index}`).value.trim();
        const prompt = document.getElementById(`style-prompt-${index}`).value.trim();
        if (name && prompt) {
            styles.push({ name, prompt });
        }
    });

    return styles;
}

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
    const schedule = artframe.schedule || {};
    const source = artframe.source || {};
    const sourceConfig = source.config || {};
    const style = artframe.style || {};
    const styleConfig = style.config || {};
    const display = artframe.display || {};
    const displayConfig = display.config || {};
    const cache = artframe.cache || {};
    const logging = artframe.logging || {};

    const formHtml = `
        <form id="config-form" class="config-form">
            <!-- Schedule Section -->
            <div class="config-section">
                <h3>📅 Schedule</h3>
                <div class="form-grid">
                    <div class="form-group">
                        <label for="schedule-time">Update Time</label>
                        <input type="time" id="schedule-time" value="${schedule.update_time || '06:00'}" required>
                        <span class="help-text">Daily time to update the display</span>
                    </div>
                    <div class="form-group">
                        <label for="schedule-timezone">Timezone</label>
                        <input type="text" id="schedule-timezone" value="${schedule.timezone || 'UTC'}" required>
                        <span class="help-text">e.g., America/New_York, Europe/London</span>
                    </div>
                </div>
            </div>

            <!-- Photo Source Section -->
            <div class="config-section">
                <h3>📷 Photo Source</h3>
                <div class="form-grid">
                    <div class="form-group">
                        <label for="source-provider">Provider</label>
                        <select id="source-provider" required onchange="updateSourceFields()">
                            <option value="immich" ${source.provider === 'immich' ? 'selected' : ''}>Immich</option>
                            <option value="none" ${source.provider === 'none' ? 'selected' : ''}>None (Disabled)</option>
                        </select>
                    </div>
                    <div id="source-dynamic-fields">
                        <!-- Dynamic fields will be inserted here -->
                    </div>
                </div>
            </div>

            <!-- Style Section -->
            <div class="config-section">
                <h3>🎨 Style Settings</h3>
                <div class="form-grid">
                    <div class="form-group">
                        <label for="style-provider">Provider</label>
                        <select id="style-provider" required>
                            <option value="nanobanana" ${style.provider === 'nanobanana' ? 'selected' : ''}>NanoBanana</option>
                            <option value="mock" ${style.provider === 'mock' ? 'selected' : ''}>Mock (Testing)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="style-api-url">API URL</label>
                        <input type="url" id="style-api-url" value="${styleConfig.api_url || ''}" placeholder="https://api.nanobanana.com">
                        <span class="help-text">NanoBanana API URL (required for NanoBanana provider)</span>
                    </div>
                    <div class="form-group">
                        <label for="style-api-key">API Key</label>
                        <input type="text" id="style-api-key" value="${styleConfig.api_key || ''}" placeholder="Enter API key">
                        <span class="help-text">NanoBanana API key (leave empty for mock testing)</span>
                    </div>
                    <div class="form-group full-width">
                        <label>Available Styles</label>
                        <div id="styles-editor" class="styles-editor">
                            ${renderStylesEditor(styleConfig.styles || [])}
                        </div>
                        <button type="button" class="btn btn-small btn-secondary" onclick="addStyle()">➕ Add Style</button>
                        <span class="help-text">Define custom art styles with detailed prompts</span>
                    </div>
                    <div class="form-group">
                        <label for="style-rotation">Rotation Mode</label>
                        <select id="style-rotation" required>
                            <option value="daily" ${styleConfig.rotation === 'daily' ? 'selected' : ''}>Daily</option>
                            <option value="random" ${styleConfig.rotation === 'random' ? 'selected' : ''}>Random</option>
                            <option value="sequential" ${styleConfig.rotation === 'sequential' ? 'selected' : ''}>Sequential</option>
                        </select>
                    </div>
                </div>
            </div>

            <!-- Display Section -->
            <div class="config-section">
                <h3>📺 Display</h3>
                <div class="form-grid">
                    <div class="form-group">
                        <label for="display-driver">Driver</label>
                        <select id="display-driver" required>
                            <option value="spectra6" ${display.driver === 'spectra6' ? 'selected' : ''}>Spectra 6</option>
                            <option value="mock" ${display.driver === 'mock' ? 'selected' : ''}>Mock (Testing)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="display-width">Width (pixels)</label>
                        <input type="number" id="display-width" value="${displayConfig.width || 600}" min="1" required onchange="updateDisplayInfo()">
                        <span class="help-text">Display width in pixels</span>
                    </div>
                    <div class="form-group">
                        <label for="display-height">Height (pixels)</label>
                        <input type="number" id="display-height" value="${displayConfig.height || 448}" min="1" required onchange="updateDisplayInfo()">
                        <span class="help-text">Display height in pixels</span>
                    </div>
                    <div class="form-group">
                        <label for="display-rotation">Rotation</label>
                        <select id="display-rotation" required onchange="updateDisplayInfo()">
                            <option value="0" ${displayConfig.rotation === 0 ? 'selected' : ''}>0°</option>
                            <option value="90" ${displayConfig.rotation === 90 ? 'selected' : ''}>90°</option>
                            <option value="180" ${displayConfig.rotation === 180 ? 'selected' : ''}>180°</option>
                            <option value="270" ${displayConfig.rotation === 270 ? 'selected' : ''}>270°</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Display Info</label>
                        <div id="display-info" class="display-info-box"></div>
                    </div>
                    <div class="form-group">
                        <label for="display-metadata">Show Metadata</label>
                        <input type="checkbox" id="display-metadata" ${displayConfig.show_metadata ? 'checked' : ''}>
                        <span class="help-text">Display photo date/location overlay</span>
                    </div>
                </div>
            </div>

            <!-- Cache Section -->
            <div class="config-section">
                <h3>💾 Cache</h3>
                <div class="form-grid">
                    <div class="form-group">
                        <label for="cache-directory">Directory</label>
                        <input type="text" id="cache-directory" value="${cache.directory || '/var/cache/artframe'}" required>
                        <span class="help-text">Path to cache directory</span>
                    </div>
                    <div class="form-group">
                        <label for="cache-max-images">Max Images</label>
                        <input type="number" id="cache-max-images" value="${cache.max_images || 100}" min="1" required>
                        <span class="help-text">Maximum cached images</span>
                    </div>
                    <div class="form-group">
                        <label for="cache-max-size">Max Size (MB)</label>
                        <input type="number" id="cache-max-size" value="${cache.max_size_mb || 500}" min="1" required>
                        <span class="help-text">Maximum cache size in MB</span>
                    </div>
                    <div class="form-group">
                        <label for="cache-retention">Retention (days)</label>
                        <input type="number" id="cache-retention" value="${cache.retention_days || 30}" min="1" required>
                        <span class="help-text">Days to keep cached images</span>
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
                    </div>
                    <div class="form-group">
                        <label for="logging-file">Log File</label>
                        <input type="text" id="logging-file" value="${logging.file || '/var/log/artframe/artframe.log'}" required>
                        <span class="help-text">Path to log file</span>
                    </div>
                </div>
            </div>
        </form>
    `;

    setElementContent('config-content', formHtml);
    updateDisplayInfo();
    updateSourceFields();
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

function getSourceConfig() {
    const provider = document.getElementById('source-provider').value;
    const fields = sourceProviderFields[provider] || [];
    const config = {};

    fields.forEach(field => {
        const element = document.getElementById(field.id);
        if (element) {
            const value = element.value;
            if (value || field.required) {
                config[field.configKey] = value || undefined;
            }
        }
    });

    return config;
}

function getFormValues() {
    const styles = collectStyles();

    return {
        artframe: {
            schedule: {
                update_time: document.getElementById('schedule-time').value,
                timezone: document.getElementById('schedule-timezone').value
            },
            source: {
                provider: document.getElementById('source-provider').value,
                config: getSourceConfig()
            },
            style: {
                provider: document.getElementById('style-provider').value,
                config: {
                    api_url: document.getElementById('style-api-url').value,
                    api_key: document.getElementById('style-api-key').value,
                    styles: styles,
                    rotation: document.getElementById('style-rotation').value
                }
            },
            display: {
                driver: document.getElementById('display-driver').value,
                config: {
                    gpio_pins: currentConfig?.artframe?.display?.config?.gpio_pins || {
                        busy: 24,
                        reset: 17,
                        dc: 25,
                        cs: 8
                    },
                    rotation: parseInt(document.getElementById('display-rotation').value),
                    show_metadata: document.getElementById('display-metadata').checked,
                    width: parseInt(document.getElementById('display-width').value),
                    height: parseInt(document.getElementById('display-height').value)
                }
            },
            cache: {
                directory: document.getElementById('cache-directory').value,
                max_images: parseInt(document.getElementById('cache-max-images').value),
                max_size_mb: parseInt(document.getElementById('cache-max-size').value),
                retention_days: parseInt(document.getElementById('cache-retention').value)
            },
            logging: {
                level: document.getElementById('logging-level').value,
                file: document.getElementById('logging-file').value
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

        const validateResult = await apiCall('/api/config', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(newConfig)
        });

        if (!validateResult.success) {
            showNotification('✗ Invalid config: ' + validateResult.error, 'error');
            return;
        }

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

    try {
        await fetch('/api/restart', { method: 'POST' });
        showNotification('✓ Restart initiated. Page will reload in 5 seconds...', 'success');

        setTimeout(() => {
            window.location.reload();
        }, 5000);
    } catch (error) {
        showNotification('✗ Restart failed: ' + error.message, 'error');
        restartBtn.disabled = false;
        restartBtn.textContent = '🔄 Restart';
    }
}

async function testSourceConnection() {
    const testBtn = document.getElementById('test-source-btn');

    testBtn.disabled = true;
    testBtn.textContent = '🔄 Testing...';

    try {
        // Get current form values
        const provider = document.getElementById('source-provider').value;
        const sourceConfig = getSourceConfig();

        const sourceData = {
            provider: provider,
            ...sourceConfig
        };

        const response = await fetch('/api/test-source', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(sourceData)
        });

        const result = await response.json();

        if (result.success && result.connection) {
            showNotification('✓ ' + result.message, 'success');
        } else if (result.success && !result.connection) {
            showNotification('✗ ' + result.message, 'error');
        } else {
            showNotification('✗ ' + (result.error || 'Test failed'), 'error');
        }

    } catch (error) {
        showNotification('✗ Connection test failed: ' + error.message, 'error');
    } finally {
        testBtn.disabled = false;
        testBtn.textContent = '🔗 Test Connection';
    }
}

// Source provider field configurations
const sourceProviderFields = {
    immich: [
        {
            id: 'source-server',
            label: 'Server URL',
            type: 'url',
            placeholder: 'https://immich.example.com',
            helpText: 'Immich server URL (required)',
            required: true,
            configKey: 'server_url'
        },
        {
            id: 'source-api-key',
            label: 'API Key',
            type: 'text',
            placeholder: 'Enter API key',
            helpText: 'Immich API key for authentication',
            required: true,
            configKey: 'api_key'
        },
        {
            id: 'source-album',
            label: 'Album ID',
            type: 'text',
            placeholder: 'Optional album ID',
            helpText: 'Optional: specific album ID to use',
            required: false,
            configKey: 'album_id'
        },
        {
            id: 'source-selection',
            label: 'Selection Mode',
            type: 'select',
            options: [
                { value: 'random', label: 'Random' },
                { value: 'newest', label: 'Newest' },
                { value: 'oldest', label: 'Oldest' }
            ],
            helpText: 'How to select photos from the source',
            required: true,
            configKey: 'selection'
        }
    ],
    none: []
};

function updateSourceFields() {
    const provider = document.getElementById('source-provider').value;
    const dynamicFields = document.getElementById('source-dynamic-fields');
    const sourceConfig = currentConfig?.artframe?.source?.config || {};

    const fields = sourceProviderFields[provider] || [];

    let html = '';

    // Add provider-specific fields
    fields.forEach(field => {
        const value = sourceConfig[field.configKey] || '';

        html += `<div class="form-group">`;
        html += `<label for="${field.id}">${field.label}</label>`;

        if (field.type === 'select') {
            html += `<select id="${field.id}" ${field.required ? 'required' : ''}>`;
            field.options.forEach(option => {
                const selected = value === option.value ? 'selected' : '';
                html += `<option value="${option.value}" ${selected}>${option.label}</option>`;
            });
            html += `</select>`;
        } else {
            html += `<input type="${field.type}" id="${field.id}" value="${value}" placeholder="${field.placeholder || ''}" ${field.required ? 'required' : ''}>`;
        }

        if (field.helpText) {
            html += `<span class="help-text">${field.helpText}</span>`;
        }
        html += `</div>`;
    });

    // Always add test connection button (except for none provider)
    if (provider !== 'none') {
        html += `
            <div class="form-group">
                <label>Test Connection</label>
                <button type="button" class="btn btn-secondary" onclick="testSourceConnection()" id="test-source-btn">
                    🔗 Test Connection
                </button>
            </div>
        `;
    }

    dynamicFields.innerHTML = html;
}

fetchConfig();