/**
 * Plugins page JavaScript
 * Handles plugin and instance management UI
 */

let currentPlugins = [];
let currentInstances = [];
let selectedPlugin = null;
let editingInstance = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    loadPlugins();
    loadInstances();
});

// Tab switching
function switchTab(tabName, event) {
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    // If called from click event, set clicked button as active
    if (event && event.target) {
        event.target.classList.add('active');
    } else {
        // If called programmatically, find the right button
        const buttons = document.querySelectorAll('.tab-btn');
        buttons.forEach((btn, index) => {
            if ((tabName === 'plugins' && index === 0) || (tabName === 'instances' && index === 1)) {
                btn.classList.add('active');
            }
        });
    }

    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${tabName}-tab`).classList.add('active');
}

// ===== Plugins Tab =====

async function loadPlugins() {
    try {
        const response = await fetch('/api/plugins');
        const result = await response.json();

        if (!result.success) {
            throw new Error(result.error);
        }

        currentPlugins = result.data;
        renderPlugins(currentPlugins);

    } catch (error) {
        console.error('Failed to load plugins:', error);
        document.getElementById('plugins-list').innerHTML = `
            <div class="error">
                <p>Failed to load plugins: ${error.message}</p>
            </div>
        `;
    }
}

function renderPlugins(plugins) {
    const container = document.getElementById('plugins-list');

    if (plugins.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <h3>No plugins found</h3>
                <p>No plugins are currently installed.</p>
            </div>
        `;
        return;
    }

    const pluginsHTML = `
        <div class="plugins-grid">
            ${plugins.map(plugin => `
                <div class="plugin-card">
                    <h3>${plugin.display_name}</h3>
                    <div class="plugin-meta">
                        ${plugin.author} • v${plugin.version}
                    </div>
                    <div class="plugin-description">
                        ${plugin.description || 'No description available'}
                    </div>
                    <button class="btn btn-primary btn-small" onclick="openCreateInstanceModal('${plugin.id}')">
                        + Create Instance
                    </button>
                </div>
            `).join('')}
        </div>
    `;

    container.innerHTML = pluginsHTML;
}

// ===== Instances Tab =====

async function loadInstances() {
    try {
        const response = await fetch('/api/plugins/instances');
        const result = await response.json();

        if (!result.success) {
            throw new Error(result.error);
        }

        currentInstances = result.data;
        renderInstances(currentInstances);

    } catch (error) {
        console.error('Failed to load instances:', error);
        document.getElementById('instances-list').innerHTML = `
            <div class="error">
                <p>Failed to load instances: ${error.message}</p>
            </div>
        `;
    }
}

function renderInstances(instances) {
    const container = document.getElementById('instances-list');

    if (instances.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <h3>No instances yet</h3>
                <p>Create a plugin instance from the Available Plugins tab to get started.</p>
            </div>
        `;
        return;
    }

    const instancesHTML = `
        <table class="instances-table">
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Plugin</th>
                    <th>Status</th>
                    <th>Created</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                ${instances.map(instance => {
                    const plugin = currentPlugins.find(p => p.id === instance.plugin_id);
                    const pluginName = plugin ? plugin.display_name : instance.plugin_id;
                    const createdDate = new Date(instance.created_at).toLocaleDateString();

                    return `
                        <tr>
                            <td><strong>${instance.name}</strong></td>
                            <td>${pluginName}</td>
                            <td>
                                <span class="status-badge ${instance.enabled ? 'enabled' : 'disabled'}">
                                    ${instance.enabled ? 'Enabled' : 'Disabled'}
                                </span>
                            </td>
                            <td>${createdDate}</td>
                            <td>
                                <div class="instance-actions">
                                    <button class="btn btn-small btn-secondary" onclick="editInstance('${instance.id}')">
                                        Edit
                                    </button>
                                    <button class="btn btn-small ${instance.enabled ? 'btn-warning' : 'btn-primary'}"
                                            onclick="toggleInstance('${instance.id}', ${instance.enabled})">
                                        ${instance.enabled ? 'Disable' : 'Enable'}
                                    </button>
                                    <button class="btn btn-small btn-secondary" onclick="testInstance('${instance.id}')">
                                        Test
                                    </button>
                                    <button class="btn btn-small btn-danger" onclick="deleteInstance('${instance.id}', '${instance.name}')">
                                        Delete
                                    </button>
                                </div>
                            </td>
                        </tr>
                    `;
                }).join('')}
            </tbody>
        </table>
    `;

    container.innerHTML = instancesHTML;
}

// ===== Instance Modal =====

async function openCreateInstanceModal(pluginId) {
    selectedPlugin = currentPlugins.find(p => p.id === pluginId);
    editingInstance = null;

    if (!selectedPlugin) {
        showNotification('Plugin not found', 'error');
        return;
    }

    // Set modal title
    document.getElementById('modal-title').textContent = `Create ${selectedPlugin.display_name} Instance`;

    // Clear form
    document.getElementById('instance-form').reset();
    document.getElementById('instance-id').value = '';
    document.getElementById('plugin-id').value = pluginId;
    document.getElementById('instance-name').value = '';

    // Load plugin settings template
    await loadPluginSettingsTemplate(pluginId, {});

    // Show modal
    document.getElementById('instance-modal').classList.add('active');
}

async function editInstance(instanceId) {
    const instance = currentInstances.find(i => i.id === instanceId);
    if (!instance) {
        showNotification('Instance not found', 'error');
        return;
    }

    selectedPlugin = currentPlugins.find(p => p.id === instance.plugin_id);
    editingInstance = instance;

    // Set modal title
    document.getElementById('modal-title').textContent = `Edit ${instance.name}`;

    // Fill form with instance data
    document.getElementById('instance-id').value = instance.id;
    document.getElementById('plugin-id').value = instance.plugin_id;
    document.getElementById('instance-name').value = instance.name;

    // Load plugin settings template with current values
    await loadPluginSettingsTemplate(instance.plugin_id, instance.settings);

    // Show modal
    document.getElementById('instance-modal').classList.add('active');
}

async function loadPluginSettingsTemplate(pluginId, currentSettings) {
    try {
        const response = await fetch(`/api/plugins/${pluginId}/settings-template`);
        const result = await response.json();

        if (!result.success) {
            throw new Error(result.error);
        }

        let template = result.data.template;

        // Step 1: Clean all Jinja2 template syntax from the HTML
        // Remove value="{{ ... }}" patterns and replace with empty value
        template = template.replace(/value="{{[^}]+}}"/g, 'value=""');
        // Remove checked conditionals
        template = template.replace(/\{%[^%]+%\}checked\{%[^%]+%\}/g, '');
        template = template.replace(/\{%\s*if[^%]+%\}checked\{%\s*endif\s*%\}/g, '');
        // Remove selected conditionals
        template = template.replace(/\{%[^%]+%\}selected\{%[^%]+%\}/g, '');
        template = template.replace(/\{%\s*if[^%]+%\}selected\{%\s*endif\s*%\}/g, '');
        // Remove any remaining Jinja2 blocks
        template = template.replace(/\{%[^%]+%\}/g, '');
        template = template.replace(/\{\{[^}]+\}\}/g, '');

        // Step 2: Insert cleaned HTML into DOM
        const container = document.getElementById('plugin-settings-container');
        container.innerHTML = template;

        // Step 3: Populate form fields from currentSettings using DOM manipulation
        if (currentSettings && typeof currentSettings === 'object') {
            populateFormFields(container, currentSettings);
        }

        // Re-execute any scripts in the template
        const scripts = container.querySelectorAll('script');
        scripts.forEach(oldScript => {
            const newScript = document.createElement('script');
            newScript.textContent = oldScript.textContent;
            oldScript.parentNode.replaceChild(newScript, oldScript);
        });

    } catch (error) {
        console.error('Failed to load settings template:', error);
        document.getElementById('plugin-settings-container').innerHTML = `
            <div class="error">
                <p>Failed to load settings: ${error.message}</p>
            </div>
        `;
    }
}

/**
 * Populate form fields from a settings object.
 * Handles input[type=text], input[type=checkbox], input[type=color],
 * input[type=number], select, and textarea elements.
 */
function populateFormFields(container, settings) {
    for (const [key, value] of Object.entries(settings)) {
        // Find elements by name or id
        const elements = container.querySelectorAll(`[name="${key}"], #${key}`);

        elements.forEach(element => {
            const tagName = element.tagName.toLowerCase();
            const inputType = element.type ? element.type.toLowerCase() : '';

            if (tagName === 'input') {
                if (inputType === 'checkbox') {
                    // Handle checkbox - check if value is truthy
                    element.checked = Boolean(value);
                } else if (inputType === 'radio') {
                    // Handle radio - check if value matches
                    element.checked = (element.value === String(value));
                } else {
                    // Handle text, number, color, etc.
                    element.value = value !== null && value !== undefined ? value : '';
                }
            } else if (tagName === 'select') {
                // Handle select - find and select the matching option
                const options = element.querySelectorAll('option');
                let found = false;
                options.forEach(option => {
                    if (option.value === String(value)) {
                        option.selected = true;
                        found = true;
                    } else {
                        option.selected = false;
                    }
                });
                // If no match found, try setting value directly
                if (!found && value !== null && value !== undefined) {
                    element.value = value;
                }
            } else if (tagName === 'textarea') {
                // Handle textarea
                element.value = value !== null && value !== undefined ? value : '';
            }
        });
    }
}

function closeInstanceModal() {
    document.getElementById('instance-modal').classList.remove('active');
    selectedPlugin = null;
    editingInstance = null;
}

// Handle instance form submission
document.getElementById('instance-form').addEventListener('submit', async function(e) {
    e.preventDefault();

    const instanceId = document.getElementById('instance-id').value;
    const pluginId = document.getElementById('plugin-id').value;
    const name = document.getElementById('instance-name').value;

    // Collect all form fields from plugin settings
    const formData = new FormData(e.target);
    const settings = {};

    for (const [key, value] of formData.entries()) {
        // Skip our internal fields
        if (key === 'instance_id' || key === 'plugin_id' || key === 'instance_name') {
            continue;
        }

        // Handle checkboxes
        const input = e.target.elements[key];
        if (input && input.type === 'checkbox') {
            settings[key] = input.checked;
        } else {
            settings[key] = value;
        }
    }

    try {
        let response;
        if (instanceId) {
            // Update existing instance
            response = await fetch(`/api/plugins/instances/${instanceId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ name, settings })
            });
        } else {
            // Create new instance
            response = await fetch('/api/plugins/instances', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ plugin_id: pluginId, name, settings })
            });
        }

        const result = await response.json();

        if (!result.success) {
            throw new Error(result.error);
        }

        // Close modal and reload instances
        closeInstanceModal();
        await loadInstances();

        // Switch to instances tab
        switchTab('instances');

        showNotification(instanceId ? 'Instance updated successfully' : 'Instance created successfully', 'success');

    } catch (error) {
        console.error('Failed to save instance:', error);
        showNotification('Failed to save instance: ' + error.message, 'error');
    }
});

// ===== Instance Actions =====

async function toggleInstance(instanceId, currentlyEnabled) {
    try {
        const action = currentlyEnabled ? 'disable' : 'enable';
        const response = await fetch(`/api/plugins/instances/${instanceId}/${action}`, {
            method: 'POST'
        });

        const result = await response.json();

        if (!result.success) {
            throw new Error(result.error);
        }

        await loadInstances();
        showNotification(`Instance ${action}d successfully`, 'success');

    } catch (error) {
        console.error('Failed to toggle instance:', error);
        showNotification('Failed to toggle instance: ' + error.message, 'error');
    }
}

async function testInstance(instanceId) {
    try {
        showNotification('Testing instance...', 'info');

        const response = await fetch(`/api/plugins/instances/${instanceId}/test`, {
            method: 'POST'
        });

        const result = await response.json();

        if (!result.success) {
            throw new Error(result.error);
        }

        showNotification('Test successful!', 'success');

    } catch (error) {
        console.error('Instance test failed:', error);
        showNotification('Test failed: ' + error.message, 'error');
    }
}

async function deleteInstance(instanceId, instanceName) {
    if (!confirm(`Are you sure you want to delete "${instanceName}"?`)) {
        return;
    }

    try {
        const response = await fetch(`/api/plugins/instances/${instanceId}`, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (!result.success) {
            throw new Error(result.error);
        }

        await loadInstances();
        showNotification('Instance deleted successfully', 'success');

    } catch (error) {
        console.error('Failed to delete instance:', error);
        showNotification('Failed to delete instance: ' + error.message, 'error');
    }
}

// ===== Utility Functions =====

function showNotification(message, type = 'info') {
    // Create toast notification
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);

    // Animate in
    setTimeout(() => toast.classList.add('visible'), 10);

    // Remove after delay
    setTimeout(() => {
        toast.classList.remove('visible');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}
