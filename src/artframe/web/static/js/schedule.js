/**
 * Schedule page JavaScript
 * Slot-based scheduling: each hour slot gets one content assignment
 */

let currentSlots = {};  // Map of "day-hour" -> {target_type, target_id}
let currentInstances = [];
let currentPlaylists = [];
let currentDefault = {};
let currentTimeInterval = null;

// Constants for timetable
const HOUR_HEIGHT = 30; // pixels per hour slot
const DAY_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
const DAY_NAMES_SHORT = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    loadSchedules();
    loadInstances();
    loadPlaylists();
    loadCurrentStatus();

    // Refresh current status every 30 seconds
    setInterval(loadCurrentStatus, 30000);

    // Update current time indicator every minute
    currentTimeInterval = setInterval(updateCurrentTimeIndicator, 60000);
});

// ===== Load Data =====

async function loadSchedules() {
    try {
        const response = await fetch('/api/schedules');
        const result = await response.json();

        if (!result.success) {
            throw new Error(result.error);
        }

        currentSlots = result.slots || {};
        currentDefault = result.default || {};

        renderTimetable();
        renderDefaultContent();
        updateStats();

    } catch (error) {
        console.error('Failed to load schedules:', error);
        document.getElementById('timetable-container').innerHTML = `
            <div class="error">
                <p>Failed to load schedules: ${error.message}</p>
            </div>
        `;
    }
}

async function loadInstances() {
    try {
        const response = await fetch('/api/plugins/instances');
        const result = await response.json();

        if (!result.success) {
            throw new Error(result.error);
        }

        currentInstances = result.data.filter(inst => inst.enabled);

    } catch (error) {
        console.error('Failed to load instances:', error);
    }
}

async function loadPlaylists() {
    try {
        const response = await fetch('/api/playlists');
        const result = await response.json();

        if (!result.success) {
            throw new Error(result.error);
        }

        currentPlaylists = result.data.filter(pl => pl.enabled);

    } catch (error) {
        console.error('Failed to load playlists:', error);
    }
}

async function loadCurrentStatus() {
    try {
        const response = await fetch('/api/schedules/current');
        const result = await response.json();

        if (!result.success) {
            throw new Error(result.error);
        }

        renderCurrentStatus(result.data);

    } catch (error) {
        console.error('Failed to load current status:', error);
    }
}

// ===== Rendering =====

function renderCurrentStatus(status) {
    const textElement = document.getElementById('current-status-text');

    if (!status || !status.has_content) {
        textElement.textContent = 'No content scheduled for this slot';
        return;
    }

    const icon = status.target_type === 'playlist' ? '📋' : '📷';
    let text = `${icon} ${status.target_name}`;

    if (status.source_type === 'default') {
        text += ' (default)';
    } else if (status.day !== undefined && status.hour !== undefined) {
        const dayName = DAY_NAMES[status.day];
        const hour = status.hour.toString().padStart(2, '0');
        text += ` (${dayName} ${hour}:00)`;
    }

    textElement.textContent = text;
}

function renderDefaultContent() {
    const select = document.getElementById('default-instance-select');

    // Build options: instances and playlists
    let options = '<option value="">None (keep last displayed)</option>';
    options += '<optgroup label="Instances">';
    options += currentInstances.map(instance => {
        const selected = currentDefault.target_type === 'instance' &&
                        currentDefault.target_id === instance.id ? 'selected' : '';
        return `<option value="instance:${instance.id}" ${selected}>📷 ${instance.name}</option>`;
    }).join('');
    options += '</optgroup>';

    options += '<optgroup label="Playlists">';
    options += currentPlaylists.map(playlist => {
        const selected = currentDefault.target_type === 'playlist' &&
                        currentDefault.target_id === playlist.id ? 'selected' : '';
        return `<option value="playlist:${playlist.id}" ${selected}>📋 ${playlist.name}</option>`;
    }).join('');
    options += '</optgroup>';

    select.innerHTML = options;
}

// ===== Timetable Rendering =====

function renderTimetable() {
    const container = document.getElementById('timetable-container');

    // Build the timetable grid
    let html = '<div class="timetable">';

    // Header row
    html += '<div class="timetable-header">';
    html += '<div class="timetable-header-cell time-header">Time</div>';
    for (let day = 0; day < 7; day++) {
        const isToday = day === getCurrentDayIndex();
        html += `
            <div class="timetable-header-cell ${isToday ? 'today' : ''}">
                ${DAY_NAMES[day]}
                ${isToday ? '<div class="day-date">Today</div>' : ''}
            </div>
        `;
    }
    html += '</div>';

    // Body with time rows
    html += '<div class="timetable-body">';
    for (let hour = 0; hour < 24; hour++) {
        html += '<div class="timetable-row">';

        // Time label
        const timeStr = `${hour.toString().padStart(2, '0')}:00`;
        html += `<div class="time-label hour-start" data-hour="${hour}">${timeStr}</div>`;

        // Day cells for this hour
        for (let day = 0; day < 7; day++) {
            const slotKey = `${day}-${hour}`;
            const slot = currentSlots[slotKey];
            const hasContent = !!slot;

            html += `
                <div class="day-column hour-start ${hasContent ? 'has-content' : ''}"
                     data-day="${day}"
                     data-hour="${hour}"
                     data-slot-key="${slotKey}"
                     onclick="onSlotClick(${day}, ${hour})">
            `;

            if (hasContent) {
                const info = getSlotInfo(slot);
                html += `
                    <div class="slot-content ${slot.target_type === 'playlist' ? 'is-playlist' : ''}"
                         style="background-color: ${getColorForSlot(slotKey)};">
                        <span class="slot-name">${info.name}</span>
                    </div>
                `;
            }

            html += '</div>';
        }

        html += '</div>';
    }
    html += '</div>';

    html += '</div>';

    container.innerHTML = html;

    // Add current time indicator
    updateCurrentTimeIndicator();

    // Render legend
    renderLegend();

    // Scroll to current time after a short delay
    setTimeout(() => scrollToCurrentTime(), 100);
}

function getSlotInfo(slot) {
    if (!slot) return { name: '', icon: '' };

    if (slot.target_type === 'playlist') {
        const playlist = currentPlaylists.find(p => p.id === slot.target_id);
        return {
            name: playlist ? playlist.name : 'Unknown',
            icon: '📋'
        };
    } else {
        const instance = currentInstances.find(i => i.id === slot.target_id);
        return {
            name: instance ? instance.name : 'Unknown',
            icon: '📷'
        };
    }
}

function getCurrentDayIndex() {
    const jsDay = new Date().getDay(); // 0=Sunday, 1=Monday, etc.
    return jsDay === 0 ? 6 : jsDay - 1; // Convert to 0=Monday
}

function updateCurrentTimeIndicator() {
    // Remove existing indicator
    const existing = document.querySelector('.current-time-line');
    if (existing) existing.remove();

    const now = new Date();
    const currentDay = getCurrentDayIndex();
    const currentHour = now.getHours();
    const currentMinute = now.getMinutes();

    // Find the cell for current day and hour
    const cell = document.querySelector(`.day-column[data-day="${currentDay}"][data-hour="${currentHour}"]`);
    if (!cell) return;

    // Create indicator line
    const indicator = document.createElement('div');
    indicator.className = 'current-time-line';

    // Position based on minute within the hour
    const topOffset = (currentMinute / 60) * HOUR_HEIGHT;

    // Get the position of the cell relative to the timetable
    const timetable = document.querySelector('.timetable');
    if (!timetable) return;

    const cellRect = cell.getBoundingClientRect();
    const timetableRect = timetable.getBoundingClientRect();

    indicator.style.top = `${cellRect.top - timetableRect.top + topOffset}px`;

    timetable.appendChild(indicator);
}

function scrollToCurrentTime() {
    const now = new Date();
    const currentHour = now.getHours();

    // Scroll to show current time in view (centered if possible)
    const wrapper = document.querySelector('.timetable-wrapper');
    const targetCell = document.querySelector(`.time-label[data-hour="${currentHour}"]`);

    if (wrapper && targetCell) {
        const wrapperRect = wrapper.getBoundingClientRect();
        const targetRect = targetCell.getBoundingClientRect();

        // Scroll to center the current hour
        const scrollTarget = targetRect.top - wrapperRect.top + wrapper.scrollTop - (wrapperRect.height / 3);
        wrapper.scrollTo({
            top: Math.max(0, scrollTarget),
            behavior: 'smooth'
        });
    }
}

function toggleCompactMode(enabled) {
    const timetable = document.querySelector('.timetable');
    if (timetable) {
        timetable.classList.toggle('compact', enabled);
    }
}

// ===== Slot Click Handler =====

function onSlotClick(day, hour) {
    const slotKey = `${day}-${hour}`;
    const existingSlot = currentSlots[slotKey];

    // Open the slot assignment modal
    openSlotModal(day, hour, existingSlot);
}

function openSlotModal(day, hour, existingSlot) {
    document.getElementById('slot-modal-title').textContent =
        `${DAY_NAMES[day]} ${hour.toString().padStart(2, '0')}:00`;
    document.getElementById('slot-day').value = day;
    document.getElementById('slot-hour').value = hour;

    // Populate content selector
    const select = document.getElementById('slot-content-select');
    let options = '<option value="">-- Empty (no content) --</option>';

    options += '<optgroup label="Plugin Instances">';
    options += currentInstances.map(instance => {
        const selected = existingSlot &&
                        existingSlot.target_type === 'instance' &&
                        existingSlot.target_id === instance.id ? 'selected' : '';
        return `<option value="instance:${instance.id}" ${selected}>📷 ${instance.name}</option>`;
    }).join('');
    options += '</optgroup>';

    options += '<optgroup label="Playlists">';
    options += currentPlaylists.map(playlist => {
        const selected = existingSlot &&
                        existingSlot.target_type === 'playlist' &&
                        existingSlot.target_id === playlist.id ? 'selected' : '';
        return `<option value="playlist:${playlist.id}" ${selected}>📋 ${playlist.name} (${playlist.items?.length || 0} items)</option>`;
    }).join('');
    options += '</optgroup>';

    select.innerHTML = options;

    // Show/hide delete button
    document.getElementById('slot-delete-btn').style.display = existingSlot ? 'inline-block' : 'none';

    document.getElementById('slot-modal').classList.add('active');
}

function closeSlotModal() {
    document.getElementById('slot-modal').classList.remove('active');
}

async function saveSlot() {
    const day = parseInt(document.getElementById('slot-day').value);
    const hour = parseInt(document.getElementById('slot-hour').value);
    const contentValue = document.getElementById('slot-content-select').value;

    try {
        if (!contentValue) {
            // Clear the slot
            await clearSlot(day, hour);
        } else {
            // Set the slot
            const [targetType, targetId] = contentValue.split(':');

            const response = await fetch('/api/schedules/slot', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    day,
                    hour,
                    target_type: targetType,
                    target_id: targetId
                })
            });

            const result = await response.json();
            if (!result.success) {
                throw new Error(result.error);
            }
        }

        closeSlotModal();
        await loadSchedules();
        showNotification('Slot updated', 'success');

    } catch (error) {
        console.error('Failed to save slot:', error);
        showNotification('Failed to save slot: ' + error.message, 'error');
    }
}

async function deleteCurrentSlot() {
    const day = parseInt(document.getElementById('slot-day').value);
    const hour = parseInt(document.getElementById('slot-hour').value);

    try {
        await clearSlot(day, hour);
        closeSlotModal();
        await loadSchedules();
        showNotification('Slot cleared', 'success');

    } catch (error) {
        console.error('Failed to clear slot:', error);
        showNotification('Failed to clear slot: ' + error.message, 'error');
    }
}

async function clearSlot(day, hour) {
    const response = await fetch('/api/schedules/slot', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ day, hour })
    });

    const result = await response.json();
    if (!result.success) {
        throw new Error(result.error);
    }
}

async function saveDefaultContent() {
    const select = document.getElementById('default-instance-select');
    const value = select.value;

    try {
        let payload = {};
        if (value) {
            const [targetType, targetId] = value.split(':');
            payload = {
                target_type: targetType,
                target_id: targetId
            };
        }

        const response = await fetch('/api/schedules/default', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const result = await response.json();

        if (!result.success) {
            throw new Error(result.error);
        }

        showNotification('Default content updated', 'success');

    } catch (error) {
        console.error('Failed to update default content:', error);
        showNotification('Failed to update default content: ' + error.message, 'error');
    }
}

async function clearAllSlots() {
    if (!confirm('Are you sure you want to clear ALL scheduled slots? This cannot be undone.')) {
        return;
    }

    try {
        const response = await fetch('/api/schedules/clear', {
            method: 'POST'
        });

        const result = await response.json();

        if (!result.success) {
            throw new Error(result.error);
        }

        await loadSchedules();
        showNotification('All slots cleared', 'success');

    } catch (error) {
        console.error('Failed to clear slots:', error);
        showNotification('Failed to clear slots: ' + error.message, 'error');
    }
}

// ===== Utility Functions =====

function getColorForSlot(slotKey) {
    const slot = currentSlots[slotKey];
    if (!slot) return '#f0f0f0';

    // Use target_id for consistent coloring
    const id = slot.target_id;
    const colors = [
        '#667eea',
        '#f093fb',
        '#4facfe',
        '#43e97b',
        '#fa709a',
        '#30cfd0',
        '#a8edea',
        '#fbc2eb',
        '#fa8bff'
    ];

    // Simple hash of ID to pick a color
    let hash = 0;
    for (let i = 0; i < id.length; i++) {
        hash = id.charCodeAt(i) + ((hash << 5) - hash);
    }
    return colors[Math.abs(hash) % colors.length];
}

function showNotification(message, type = 'info') {
    // Simple notification - could be enhanced with a proper toast system
    alert(message);
}

function renderLegend() {
    const legendContainer = document.getElementById('schedule-legend');

    // Collect unique content items
    const contentMap = {};
    Object.values(currentSlots).forEach(slot => {
        const key = `${slot.target_type}:${slot.target_id}`;
        if (!contentMap[key]) {
            contentMap[key] = slot;
        }
    });

    const items = Object.entries(contentMap);

    if (items.length === 0) {
        legendContainer.innerHTML = '<p class="hint">Click on any slot to assign content</p>';
        return;
    }

    let legendHTML = '<h4>Legend</h4><div class="legend-grid">';

    items.forEach(([key, slot]) => {
        const info = getSlotInfo(slot);
        // Find a slot with this content to get the color
        const slotKey = Object.keys(currentSlots).find(k =>
            currentSlots[k].target_type === slot.target_type &&
            currentSlots[k].target_id === slot.target_id
        );
        const color = getColorForSlot(slotKey);
        const icon = slot.target_type === 'playlist' ? '📋' : '📷';

        legendHTML += `
            <div class="legend-item">
                <span class="legend-color" style="background-color: ${color};"></span>
                <span>${icon} ${info.name}</span>
            </div>
        `;
    });

    // Add default legend if set
    if (currentDefault.target_id) {
        const defaultInfo = getSlotInfo(currentDefault);
        const icon = currentDefault.target_type === 'playlist' ? '📋' : '📷';
        legendHTML += `
            <div class="legend-item">
                <span class="legend-color" style="background-color: #f0f0f0; border: 1px solid #ddd;"></span>
                <span>Default: ${icon} ${defaultInfo.name}</span>
            </div>
        `;
    }

    legendHTML += '</div>';
    legendContainer.innerHTML = legendHTML;
}

// ===== Stats =====

function updateStats() {
    const filledSlots = Object.keys(currentSlots).length;
    const totalSlots = 7 * 24; // 7 days * 24 hours

    document.getElementById('stat-entries').textContent = filledSlots;

    const coveragePercent = Math.round((filledSlots / totalSlots) * 100);
    document.getElementById('stat-coverage').textContent = coveragePercent + '%';
}
