/**
 * Schedule page JavaScript
 * Handles schedule entry management and timeline visualization
 */

let currentEntries = [];
let currentInstances = [];
let currentConfig = {};
let editingEntry = null;
let selectedDay = new Date().getDay() === 0 ? 6 : new Date().getDay() - 1; // Convert to 0=Monday
let currentViewMode = 'week';
let weeklyScheduleData = {}; // Cached schedule data for all days

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    loadSchedules();
    loadInstances();
    loadCurrentStatus();

    // Refresh current status every 30 seconds
    setInterval(loadCurrentStatus, 30000);

    // Set initial view mode
    currentViewMode = 'week';
});

// ===== Load Data =====

async function loadSchedules() {
    try {
        const response = await fetch('/api/schedules');
        const result = await response.json();

        if (!result.success) {
            throw new Error(result.error);
        }

        currentEntries = result.data;
        currentConfig = result.config;

        renderEntries(currentEntries);
        renderDefaultContent();

        // Render based on current view mode
        if (currentViewMode === 'week') {
            await renderWeeklyView();
        } else {
            await renderTimeline(selectedDay);
        }

        // Update stats
        updateStats();

    } catch (error) {
        console.error('Failed to load schedules:', error);
        document.getElementById('entries-list').innerHTML = `
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

    if (status.status === 'no_schedule') {
        textElement.textContent = status.message;
    } else if (status.status === 'error') {
        textElement.textContent = '⚠️ ' + status.message;
    } else {
        let text = status.instance_name;
        if (status.is_default) {
            text += ' (default)';
        } else if (status.entry_name) {
            text += ` - ${status.entry_name} (${status.start_time} - ${status.end_time})`;
        }
        textElement.textContent = text;
    }
}

function renderDefaultContent() {
    const select = document.getElementById('default-instance-select');

    const options = currentInstances.map(instance => {
        const selected = instance.id === currentConfig.default_instance_id ? 'selected' : '';
        return `<option value="${instance.id}" ${selected}>${instance.name}</option>`;
    }).join('');

    select.innerHTML = `<option value="">None (keep last displayed)</option>` + options;
}

function renderEntries(entries) {
    const container = document.getElementById('entries-list');

    if (entries.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <h3>No schedule entries yet</h3>
                <p>Add your first entry to start scheduling content!</p>
                <button class="btn btn-primary" onclick="openCreateEntryModal()">
                    ➕ Add Schedule Entry
                </button>
            </div>
        `;
        return;
    }

    // Sort by start time
    entries.sort((a, b) => a.start_time.localeCompare(b.start_time));

    const entriesHTML = `
        <table class="entries-table">
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Time</th>
                    <th>Days</th>
                    <th>Content</th>
                    <th>Priority</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                ${entries.map(entry => {
                    const instance = currentInstances.find(i => i.id === entry.instance_id);
                    const instanceName = instance ? instance.name : 'Unknown';
                    const daysDisplay = formatDays(entry.days_of_week);

                    return `
                        <tr class="${!entry.enabled ? 'disabled' : ''}">
                            <td><strong>${entry.name}</strong></td>
                            <td>${entry.start_time} - ${entry.end_time}</td>
                            <td>${daysDisplay}</td>
                            <td>${instanceName}</td>
                            <td><span class="priority-badge">${entry.priority}</span></td>
                            <td>
                                <div class="entry-actions">
                                    <button class="btn btn-small btn-secondary" onclick="editEntry('${entry.id}')">
                                        Edit
                                    </button>
                                    <button class="btn btn-small btn-danger" onclick="deleteEntry('${entry.id}', '${entry.name}')">
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

    container.innerHTML = entriesHTML;
}

async function renderTimeline(day) {
    selectedDay = day;

    // Update day selector buttons
    const buttons = document.querySelectorAll('.day-selector button');
    buttons.forEach((btn, index) => {
        if (index === day) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    try {
        const response = await fetch(`/api/schedules/timeline?day=${day}`);
        const result = await response.json();

        if (!result.success) {
            throw new Error(result.error);
        }

        renderTimelineView(result.data);

    } catch (error) {
        console.error('Failed to load timeline:', error);
    }
}

function renderTimelineView(data) {
    const container = document.getElementById('timeline-container');

    if (data.entries.length === 0 && !data.default) {
        container.innerHTML = `
            <div class="empty-state">
                <p>No schedule entries for this day</p>
            </div>
        `;
        return;
    }

    // Build timeline visualization
    let timelineHTML = '<div class="timeline">';

    // Add blocks for each entry
    data.entries.forEach((entry, index) => {
        const startMinutes = timeToMinutes(entry.start_time);
        const endMinutes = timeToMinutes(entry.end_time);

        // Calculate position and width (24 hours = 100%)
        const left = (startMinutes / 1440) * 100;
        const width = ((endMinutes - startMinutes) / 1440) * 100;

        const color = getColorForIndex(index);

        timelineHTML += `
            <div class="timeline-block"
                 style="left: ${left}%; width: ${width}%; background-color: ${color};"
                 onclick="editEntry('${entry.entry_id}')"
                 title="${entry.entry_name}: ${entry.instance_name} (${entry.start_time} - ${entry.end_time})">
                ${entry.entry_name}
            </div>
        `;
    });

    timelineHTML += '</div>';

    // Add time labels
    timelineHTML += `
        <div class="timeline-labels">
            <span>00:00</span>
            <span>04:00</span>
            <span>08:00</span>
            <span>12:00</span>
            <span>16:00</span>
            <span>20:00</span>
            <span>24:00</span>
        </div>
    `;

    // Add legend
    timelineHTML += '<div class="timeline-legend">';
    data.entries.forEach((entry, index) => {
        const color = getColorForIndex(index);
        timelineHTML += `
            <div class="legend-item">
                <span class="legend-color" style="background-color: ${color};"></span>
                <span>${entry.entry_name}</span>
            </div>
        `;
    });

    if (data.default) {
        timelineHTML += `
            <div class="legend-item">
                <span class="legend-color" style="background-color: #cccccc;"></span>
                <span>Default: ${data.default.instance_name}</span>
            </div>
        `;
    }

    timelineHTML += '</div>';

    container.innerHTML = timelineHTML;
}

// ===== Create/Edit Entry =====

function openCreateEntryModal() {
    editingEntry = null;

    document.getElementById('entry-modal-title').textContent = 'Add Schedule Entry';
    document.getElementById('entry-form').reset();
    document.getElementById('entry-id').value = '';
    document.getElementById('entry-priority').value = '5';

    // Uncheck all day checkboxes
    document.querySelectorAll('.day-checkbox').forEach(cb => cb.checked = false);

    populateInstanceSelect();
    document.getElementById('entry-modal').classList.add('active');
}

function editEntry(entryId) {
    const entry = currentEntries.find(e => e.id === entryId);
    if (!entry) {
        alert('Schedule entry not found');
        return;
    }

    editingEntry = entry;

    document.getElementById('entry-modal-title').textContent = `Edit ${entry.name}`;
    document.getElementById('entry-id').value = entry.id;
    document.getElementById('entry-name').value = entry.name;
    document.getElementById('entry-instance').value = entry.instance_id;
    document.getElementById('entry-start-time').value = entry.start_time;
    document.getElementById('entry-end-time').value = entry.end_time;
    document.getElementById('entry-priority').value = entry.priority;

    // Set day checkboxes
    document.querySelectorAll('.day-checkbox').forEach(cb => {
        cb.checked = entry.days_of_week.includes(parseInt(cb.value));
    });

    populateInstanceSelect();
    document.getElementById('entry-modal').classList.add('active');
}

function closeEntryModal() {
    document.getElementById('entry-modal').classList.remove('active');
    editingEntry = null;
}

function populateInstanceSelect() {
    const select = document.getElementById('entry-instance');

    const options = currentInstances.map(instance => {
        return `<option value="${instance.id}">${instance.name}</option>`;
    }).join('');

    select.innerHTML = `<option value="">Select a plugin instance...</option>` + options;
}

async function saveEntry(event) {
    event.preventDefault();

    const entryId = document.getElementById('entry-id').value;
    const name = document.getElementById('entry-name').value;
    const instanceId = document.getElementById('entry-instance').value;
    const startTime = document.getElementById('entry-start-time').value;
    const endTime = document.getElementById('entry-end-time').value;
    const priority = parseInt(document.getElementById('entry-priority').value);

    // Get selected days
    const daysOfWeek = [];
    document.querySelectorAll('.day-checkbox:checked').forEach(cb => {
        daysOfWeek.push(parseInt(cb.value));
    });

    if (daysOfWeek.length === 0) {
        alert('Please select at least one day');
        return;
    }

    try {
        let response;
        if (entryId) {
            // Update existing entry
            response = await fetch(`/api/schedules/${entryId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name,
                    instance_id: instanceId,
                    start_time: startTime,
                    end_time: endTime,
                    days_of_week: daysOfWeek,
                    priority
                })
            });
        } else {
            // Create new entry
            response = await fetch('/api/schedules', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name,
                    instance_id: instanceId,
                    start_time: startTime,
                    end_time: endTime,
                    days_of_week: daysOfWeek,
                    priority
                })
            });
        }

        const result = await response.json();

        if (!result.success) {
            throw new Error(result.error);
        }

        closeEntryModal();
        await loadSchedules();

        showNotification(entryId ? 'Schedule entry updated' : 'Schedule entry created', 'success');

    } catch (error) {
        console.error('Failed to save entry:', error);
        showNotification('Failed to save entry: ' + error.message, 'error');
    }
}

async function deleteEntry(entryId, entryName) {
    if (!confirm(`Are you sure you want to delete "${entryName}"?`)) {
        return;
    }

    try {
        const response = await fetch(`/api/schedules/${entryId}`, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (!result.success) {
            throw new Error(result.error);
        }

        await loadSchedules();
        showNotification('Schedule entry deleted', 'success');

    } catch (error) {
        console.error('Failed to delete entry:', error);
        showNotification('Failed to delete entry: ' + error.message, 'error');
    }
}

async function saveDefaultContent() {
    const instanceId = document.getElementById('default-instance-select').value;

    try {
        const response = await fetch('/api/schedules/config', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                default_instance_id: instanceId || null
            })
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

// ===== Timeline Controls =====

function changeDay(day) {
    renderTimeline(day);
}

// ===== Utility Functions =====

function formatDays(daysArray) {
    const dayNames = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

    if (daysArray.length === 7) {
        return '<span class="days-badge">Every day</span>';
    }

    if (daysArray.length === 5 && !daysArray.includes(5) && !daysArray.includes(6)) {
        return '<span class="days-badge">Weekdays</span>';
    }

    if (daysArray.length === 2 && daysArray.includes(5) && daysArray.includes(6)) {
        return '<span class="days-badge">Weekends</span>';
    }

    return daysArray.sort().map(d => `<span class="days-badge">${dayNames[d]}</span>`).join(' ');
}

function timeToMinutes(timeStr) {
    const [hours, minutes] = timeStr.split(':').map(Number);
    return hours * 60 + minutes;
}

function getColorForIndex(index) {
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
    return colors[index % colors.length];
}

function showNotification(message, type = 'info') {
    // Simple notification - could be enhanced with a proper toast system
    alert(message);
}

// ===== Weekly View Functions =====

async function renderWeeklyView() {
    const container = document.getElementById('weekly-grid-container');

    try {
        // Load schedule for all 7 days
        const promises = [];
        for (let day = 0; day < 7; day++) {
            promises.push(fetch(`/api/schedules/timeline?day=${day}`).then(r => r.json()));
        }

        const results = await Promise.all(promises);
        weeklyScheduleData = {};
        results.forEach((result, index) => {
            if (result.success) {
                weeklyScheduleData[index] = result.data;
            }
        });

        // Render the grid
        renderWeeklyGrid();

    } catch (error) {
        console.error('Failed to load weekly view:', error);
        container.innerHTML = `<div class="error">Failed to load weekly schedule</div>`;
    }
}

function renderWeeklyGrid() {
    const container = document.getElementById('weekly-grid-container');
    const dayNames = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

    // Build grid HTML
    let gridHTML = '<div class="weekly-grid">';

    // Header row - empty cell + hours
    gridHTML += '<div class="grid-cell grid-header"></div>';
    for (let hour = 0; hour < 24; hour++) {
        gridHTML += `<div class="grid-cell grid-header">${hour}:00</div>`;
    }

    // Day rows
    for (let day = 0; day < 7; day++) {
        // Day label
        gridHTML += `<div class="grid-cell grid-day-label">${dayNames[day]}</div>`;

        // Hour cells
        const dayData = weeklyScheduleData[day];
        for (let hour = 0; hour < 24; hour++) {
            const content = getContentForHour(dayData, hour);
            const color = content.entry ? getColorForEntry(content.entry.entry_id) : '';
            const bgStyle = content.entry ? `background-color: ${color};` : '';
            const className = content.entry ? 'grid-content-cell has-content' : 'grid-content-cell default';
            const title = content.entry ?
                `${content.entry.entry_name}: ${content.entry.instance_name}` :
                (content.default ? `Default: ${content.default}` : 'Unscheduled');

            gridHTML += `
                <div class="${className}"
                     style="${bgStyle}"
                     title="${title}"
                     onclick="${content.entry ? `editEntry('${content.entry.entry_id}')` : ''}">
                    ${content.label}
                </div>
            `;
        }
    }

    gridHTML += '</div>';

    container.innerHTML = gridHTML;

    // Render legend
    renderLegend();
}

function getContentForHour(dayData, hour) {
    if (!dayData || !dayData.entries) {
        return {label: '', entry: null, default: null};
    }

    // Check if any entry covers this hour
    const hourStr = `${hour.toString().padStart(2, '0')}:00`;
    const nextHourStr = `${((hour + 1) % 24).toString().padStart(2, '0')}:00`;

    for (const entry of dayData.entries) {
        if (timeInHourRange(hourStr, entry.start_time, entry.end_time)) {
            return {
                label: entry.instance_name,
                entry: entry,
                default: null
            };
        }
    }

    // No entry, check for default
    if (dayData.default) {
        return {
            label: dayData.default.instance_name,
            entry: null,
            default: dayData.default.instance_name
        };
    }

    return {label: '-', entry: null, default: null};
}

function timeInHourRange(hourStr, startTime, endTime) {
    const hour = parseInt(hourStr.split(':')[0]);
    const startHour = parseInt(startTime.split(':')[0]);
    const startMin = parseInt(startTime.split(':')[1]);
    const endHour = parseInt(endTime.split(':')[0]);
    const endMin = parseInt(endTime.split(':')[1]);

    // Hour falls within the range
    if (startHour <= endHour) {
        // Normal range (e.g., 08:00 - 17:00)
        if (hour > startHour && hour < endHour) return true;
        if (hour === startHour && startMin === 0) return true;
        if (hour === startHour && startMin > 0 && hour < endHour) return true;
        return false;
    } else {
        // Overnight range (e.g., 22:00 - 02:00)
        return hour >= startHour || hour < endHour;
    }
}

function getColorForEntry(entryId) {
    // Get consistent color for an entry ID
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

    // Simple hash of entry ID to pick a color
    let hash = 0;
    for (let i = 0; i < entryId.length; i++) {
        hash = entryId.charCodeAt(i) + ((hash << 5) - hash);
    }
    return colors[Math.abs(hash) % colors.length];
}

function renderLegend() {
    const legendContainer = document.getElementById('schedule-legend');

    if (currentEntries.length === 0) {
        legendContainer.innerHTML = '';
        return;
    }

    let legendHTML = '<h4>Legend</h4><div class="legend-grid">';

    // Add entry legends
    currentEntries.forEach(entry => {
        const instance = currentInstances.find(i => i.id === entry.instance_id);
        if (instance && entry.enabled) {
            const color = getColorForEntry(entry.id);
            legendHTML += `
                <div class="legend-item">
                    <span class="legend-color" style="background-color: ${color};"></span>
                    <span>${entry.name}</span>
                </div>
            `;
        }
    });

    // Add default legend
    if (currentConfig.default_instance_id) {
        const defaultInstance = currentInstances.find(i => i.id === currentConfig.default_instance_id);
        if (defaultInstance) {
            legendHTML += `
                <div class="legend-item">
                    <span class="legend-color" style="background-color: #f0f0f0; border: 1px solid #ddd;"></span>
                    <span>Default: ${defaultInstance.name}</span>
                </div>
            `;
        }
    }

    legendHTML += '</div>';
    legendContainer.innerHTML = legendHTML;
}

// ===== View Mode Switching =====

function changeViewMode(mode) {
    currentViewMode = mode;

    if (mode === 'week') {
        document.getElementById('week-view').style.display = 'block';
        document.getElementById('day-view').style.display = 'none';
        renderWeeklyView();
    } else {
        document.getElementById('week-view').style.display = 'none';
        document.getElementById('day-view').style.display = 'block';
        renderTimeline(selectedDay);
    }
}

// ===== Stats =====

function updateStats() {
    document.getElementById('stat-entries').textContent = currentEntries.length;

    // Calculate coverage (rough estimate)
    const totalSlots = 7 * 24; // 7 days * 24 hours
    let coveredSlots = 0;

    // Count unique hour slots covered
    for (let day = 0; day < 7; day++) {
        for (let hour = 0; hour < 24; hour++) {
            const dayData = weeklyScheduleData[day];
            if (dayData && dayData.entries) {
                const hourStr = `${hour.toString().padStart(2, '0')}:00`;
                for (const entry of dayData.entries) {
                    if (timeInHourRange(hourStr, entry.start_time, entry.end_time)) {
                        coveredSlots++;
                        break;
                    }
                }
            }
        }
    }

    const coveragePercent = Math.round((coveredSlots / totalSlots) * 100);
    document.getElementById('stat-coverage').textContent = coveragePercent + '%';
}
