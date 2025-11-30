/**
 * Schedule page JavaScript
 * Slot-based scheduling: each hour slot gets one content assignment
 */

let currentSlots = {};  // Map of "day-hour" -> {target_type, target_id}
let currentInstances = [];
let currentPlaylists = [];
let currentTimeInterval = null;

// Multi-select state
let selectedSlots = new Set();  // Set of "day-hour" keys
let isSelecting = false;
let selectionStart = null;

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

    // Global mouse up to end selection
    document.addEventListener('mouseup', onMouseUp);

    // Escape key to clear selection
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            clearSelection();
        }
    });
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

        renderTimetable();

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

    if (status.day !== undefined && status.hour !== undefined) {
        const dayName = DAY_NAMES[status.day];
        const hour = status.hour.toString().padStart(2, '0');
        text += ` (${dayName} ${hour}:00)`;
    }

    textElement.textContent = text;
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
            const isSelected = selectedSlots.has(slotKey);

            html += `
                <div class="day-column hour-start ${hasContent ? 'has-content' : ''} ${isSelected ? 'selected' : ''}"
                     data-day="${day}"
                     data-hour="${hour}"
                     data-slot-key="${slotKey}"
                     onmousedown="onSlotMouseDown(event, ${day}, ${hour})"
                     onmouseenter="onSlotMouseEnter(event, ${day}, ${hour})">
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

    // Update selection toolbar
    updateSelectionToolbar();

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

// ===== Multi-Select Handlers =====

function onSlotMouseDown(event, day, hour) {
    event.preventDefault();

    const slotKey = `${day}-${hour}`;

    if (event.shiftKey && selectionStart) {
        // Shift-click: extend selection from start to here
        extendSelection(day, hour);
    } else if (event.ctrlKey || event.metaKey) {
        // Ctrl/Cmd-click: toggle individual slot
        toggleSlotSelection(slotKey);
        selectionStart = { day, hour };
    } else {
        // Regular click: start new selection
        clearSelection();
        selectedSlots.add(slotKey);
        selectionStart = { day, hour };
        isSelecting = true;
        updateCellSelection(slotKey, true);
    }

    updateSelectionToolbar();
}

function onSlotMouseEnter(event, day, hour) {
    if (!isSelecting) return;

    // Extend selection to this cell (rectangular selection)
    extendSelection(day, hour);
}

function onMouseUp() {
    if (isSelecting) {
        isSelecting = false;

        // If only one slot selected and it was a simple click, open modal
        if (selectedSlots.size === 1) {
            const slotKey = [...selectedSlots][0];
            const [d, h] = slotKey.split('-').map(Number);
            clearSelection();
            openSlotModal(d, h, currentSlots[slotKey]);
        }
    }
}

function extendSelection(endDay, endHour) {
    if (!selectionStart) return;

    // Calculate rectangular selection
    const minDay = Math.min(selectionStart.day, endDay);
    const maxDay = Math.max(selectionStart.day, endDay);
    const minHour = Math.min(selectionStart.hour, endHour);
    const maxHour = Math.max(selectionStart.hour, endHour);

    // Clear and rebuild selection
    const oldSelection = new Set(selectedSlots);
    selectedSlots.clear();

    for (let d = minDay; d <= maxDay; d++) {
        for (let h = minHour; h <= maxHour; h++) {
            selectedSlots.add(`${d}-${h}`);
        }
    }

    // Update visual state
    oldSelection.forEach(key => {
        if (!selectedSlots.has(key)) {
            updateCellSelection(key, false);
        }
    });
    selectedSlots.forEach(key => {
        updateCellSelection(key, true);
    });

    updateSelectionToolbar();
}

function toggleSlotSelection(slotKey) {
    if (selectedSlots.has(slotKey)) {
        selectedSlots.delete(slotKey);
        updateCellSelection(slotKey, false);
    } else {
        selectedSlots.add(slotKey);
        updateCellSelection(slotKey, true);
    }
}

function updateCellSelection(slotKey, isSelected) {
    const cell = document.querySelector(`.day-column[data-slot-key="${slotKey}"]`);
    if (cell) {
        cell.classList.toggle('selected', isSelected);
    }
}

function clearSelection() {
    selectedSlots.forEach(key => {
        updateCellSelection(key, false);
    });
    selectedSlots.clear();
    selectionStart = null;
    updateSelectionToolbar();
}

function updateSelectionToolbar() {
    const toolbar = document.getElementById('selection-toolbar');
    const countSpan = document.getElementById('selection-count');

    if (selectedSlots.size > 1) {
        toolbar.classList.add('visible');
        countSpan.textContent = selectedSlots.size;
    } else {
        toolbar.classList.remove('visible');
    }
}

// ===== Bulk Operations =====

function openBulkAssignModal() {
    if (selectedSlots.size === 0) return;

    document.getElementById('bulk-slot-count').textContent = selectedSlots.size;

    // Populate content selector
    const select = document.getElementById('bulk-content-select');
    let options = '<option value="">-- Select content --</option>';

    options += '<optgroup label="Plugin Instances">';
    options += currentInstances.map(instance => {
        return `<option value="instance:${instance.id}">📷 ${instance.name}</option>`;
    }).join('');
    options += '</optgroup>';

    options += '<optgroup label="Playlists">';
    options += currentPlaylists.map(playlist => {
        return `<option value="playlist:${playlist.id}">📋 ${playlist.name}</option>`;
    }).join('');
    options += '</optgroup>';

    select.innerHTML = options;

    document.getElementById('bulk-modal').classList.add('active');
}

function closeBulkModal() {
    document.getElementById('bulk-modal').classList.remove('active');
}

async function saveBulkSlots() {
    const contentValue = document.getElementById('bulk-content-select').value;

    if (!contentValue) {
        showNotification('Please select content to assign', 'error');
        return;
    }

    const [targetType, targetId] = contentValue.split(':');

    // Build slots array
    const slots = [...selectedSlots].map(key => {
        const [day, hour] = key.split('-').map(Number);
        return { day, hour, target_type: targetType, target_id: targetId };
    });

    try {
        const response = await fetch('/api/schedules/slots/bulk', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ slots })
        });

        const result = await response.json();
        if (!result.success) {
            throw new Error(result.error);
        }

        closeBulkModal();
        clearSelection();
        await loadSchedules();
        showNotification(`Assigned content to ${slots.length} slots`, 'success');

    } catch (error) {
        console.error('Failed to bulk assign:', error);
        showNotification('Failed to assign slots: ' + error.message, 'error');
    }
}

async function clearSelectedSlots() {
    if (selectedSlots.size === 0) return;

    if (!confirm(`Clear ${selectedSlots.size} selected slots?`)) {
        return;
    }

    try {
        // Clear each slot individually (could add bulk clear endpoint)
        for (const key of selectedSlots) {
            const [day, hour] = key.split('-').map(Number);
            await clearSlot(day, hour);
        }

        clearSelection();
        await loadSchedules();
        showNotification('Selected slots cleared', 'success');

    } catch (error) {
        console.error('Failed to clear slots:', error);
        showNotification('Failed to clear slots: ' + error.message, 'error');
    }
}

// ===== Single Slot Modal =====

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
        legendContainer.innerHTML = '<p class="hint">Click and drag to select multiple slots</p>';
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

    legendHTML += '</div>';
    legendContainer.innerHTML = legendHTML;
}
