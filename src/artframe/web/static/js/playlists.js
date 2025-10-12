/**
 * Playlists page JavaScript
 * Handles playlist creation, editing, and management
 */

let currentPlaylists = [];
let currentInstances = [];
let editingPlaylist = null;
let playlistItems = [];  // Current items in the editor
let activePlaylistId = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    loadPlaylists();
    loadInstances();
});

// ===== Load Data =====

async function loadPlaylists() {
    try {
        const response = await fetch('/api/playlists');
        const result = await response.json();

        if (!result.success) {
            throw new Error(result.error);
        }

        currentPlaylists = result.data;
        activePlaylistId = result.active_playlist_id;

        renderPlaylists(currentPlaylists);
        renderActiveBanner();

    } catch (error) {
        console.error('Failed to load playlists:', error);
        document.getElementById('playlists-list').innerHTML = `
            <div class="error">
                <p>Failed to load playlists: ${error.message}</p>
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

// ===== Rendering =====

function renderActiveBanner() {
    const banner = document.getElementById('active-playlist-banner');
    const nameElement = document.getElementById('active-playlist-name');

    if (activePlaylistId) {
        const activePlaylist = currentPlaylists.find(p => p.id === activePlaylistId);
        if (activePlaylist) {
            nameElement.textContent = `Active: ${activePlaylist.name}`;
            banner.style.display = 'flex';
        } else {
            banner.style.display = 'none';
        }
    } else {
        banner.style.display = 'none';
    }
}

function renderPlaylists(playlists) {
    const container = document.getElementById('playlists-list');

    if (playlists.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <h3>No playlists yet</h3>
                <p>Create your first playlist to start orchestrating content!</p>
                <button class="btn btn-primary" onclick="openCreatePlaylistModal()">
                    ➕ Create Playlist
                </button>
            </div>
        `;
        return;
    }

    const playlistsHTML = `
        <table class="playlists-table">
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Items</th>
                    <th>Status</th>
                    <th>Created</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                ${playlists.map(playlist => {
                    const createdDate = new Date(playlist.created_at).toLocaleDateString();
                    const isActive = playlist.id === activePlaylistId;

                    return `
                        <tr>
                            <td>
                                <strong>${playlist.name}</strong>
                                ${playlist.description ? `<br><small style="color: #666;">${playlist.description}</small>` : ''}
                            </td>
                            <td>
                                <span class="playlist-items-count">
                                    ${playlist.items.length} item${playlist.items.length !== 1 ? 's' : ''}
                                </span>
                            </td>
                            <td>
                                ${isActive ? '<span class="active-badge">Active</span>' : ''}
                                ${!playlist.enabled ? '<span class="status-badge disabled">Disabled</span>' : ''}
                            </td>
                            <td>${createdDate}</td>
                            <td>
                                <div class="playlist-actions">
                                    ${!isActive && playlist.enabled ? `
                                        <button class="btn btn-small btn-success" onclick="activatePlaylist('${playlist.id}')">
                                            Activate
                                        </button>
                                    ` : ''}
                                    <button class="btn btn-small btn-secondary" onclick="editPlaylist('${playlist.id}')">
                                        Edit
                                    </button>
                                    <button class="btn btn-small btn-danger" onclick="deletePlaylist('${playlist.id}', '${playlist.name}')">
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

    container.innerHTML = playlistsHTML;
}

// ===== Create/Edit Playlist =====

function openCreatePlaylistModal() {
    editingPlaylist = null;
    playlistItems = [];

    document.getElementById('playlist-modal-title').textContent = 'Create Playlist';
    document.getElementById('playlist-form').reset();
    document.getElementById('playlist-id').value = '';
    document.getElementById('playlist-name').value = '';
    document.getElementById('playlist-description').value = '';

    renderPlaylistItems();
    populateInstanceSelect();

    document.getElementById('playlist-modal').classList.add('active');
}

function editPlaylist(playlistId) {
    const playlist = currentPlaylists.find(p => p.id === playlistId);
    if (!playlist) {
        alert('Playlist not found');
        return;
    }

    editingPlaylist = playlist;
    playlistItems = [...playlist.items];

    document.getElementById('playlist-modal-title').textContent = `Edit ${playlist.name}`;
    document.getElementById('playlist-id').value = playlist.id;
    document.getElementById('playlist-name').value = playlist.name;
    document.getElementById('playlist-description').value = playlist.description;

    renderPlaylistItems();
    populateInstanceSelect();

    document.getElementById('playlist-modal').classList.add('active');
}

function closePlaylistModal() {
    document.getElementById('playlist-modal').classList.remove('active');
    editingPlaylist = null;
    playlistItems = [];
}

function populateInstanceSelect() {
    const select = document.getElementById('add-instance-select');

    const options = currentInstances.map(instance => {
        return `<option value="${instance.id}">${instance.name}</option>`;
    }).join('');

    select.innerHTML = `<option value="">Select a plugin instance...</option>` + options;
}

function renderPlaylistItems() {
    const container = document.getElementById('playlist-items-container');

    if (playlistItems.length === 0) {
        container.innerHTML = '<p class="empty-playlist">No items yet. Add plugin instances below.</p>';
        return;
    }

    const itemsHTML = playlistItems.map((item, index) => {
        const instance = currentInstances.find(i => i.id === item.instance_id);
        const instanceName = instance ? instance.name : 'Unknown Instance';
        const duration = formatDuration(item.duration_seconds);

        return `
            <div class="playlist-item" data-index="${index}">
                <div class="playlist-item-info">
                    <div class="playlist-item-name">${instanceName}</div>
                    <div class="playlist-item-duration">Duration: ${duration}</div>
                </div>
                <div class="playlist-item-actions">
                    ${index > 0 ? `<button type="button" class="btn btn-small btn-secondary" onclick="moveItemUp(${index})">↑</button>` : ''}
                    ${index < playlistItems.length - 1 ? `<button type="button" class="btn btn-small btn-secondary" onclick="moveItemDown(${index})">↓</button>` : ''}
                    <button type="button" class="btn btn-small btn-danger" onclick="removePlaylistItem(${index})">Remove</button>
                </div>
            </div>
        `;
    }).join('');

    container.innerHTML = itemsHTML;
}

function addItemToPlaylist() {
    const instanceId = document.getElementById('add-instance-select').value;
    const duration = parseInt(document.getElementById('add-duration-input').value);

    if (!instanceId) {
        alert('Please select a plugin instance');
        return;
    }

    if (!duration || duration < 1) {
        alert('Please enter a valid duration');
        return;
    }

    playlistItems.push({
        instance_id: instanceId,
        duration_seconds: duration,
        order: playlistItems.length
    });

    renderPlaylistItems();

    // Reset form
    document.getElementById('add-instance-select').value = '';
    document.getElementById('add-duration-input').value = '3600';
}

function removePlaylistItem(index) {
    playlistItems.splice(index, 1);

    // Re-order remaining items
    playlistItems.forEach((item, i) => {
        item.order = i;
    });

    renderPlaylistItems();
}

function moveItemUp(index) {
    if (index === 0) return;

    const temp = playlistItems[index];
    playlistItems[index] = playlistItems[index - 1];
    playlistItems[index - 1] = temp;

    // Update orders
    playlistItems.forEach((item, i) => {
        item.order = i;
    });

    renderPlaylistItems();
}

function moveItemDown(index) {
    if (index === playlistItems.length - 1) return;

    const temp = playlistItems[index];
    playlistItems[index] = playlistItems[index + 1];
    playlistItems[index + 1] = temp;

    // Update orders
    playlistItems.forEach((item, i) => {
        item.order = i;
    });

    renderPlaylistItems();
}

async function savePlaylist(event) {
    event.preventDefault();

    const playlistId = document.getElementById('playlist-id').value;
    const name = document.getElementById('playlist-name').value;
    const description = document.getElementById('playlist-description').value;

    try {
        let response;
        if (playlistId) {
            // Update existing playlist
            response = await fetch(`/api/playlists/${playlistId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name,
                    description,
                    items: playlistItems
                })
            });
        } else {
            // Create new playlist
            response = await fetch('/api/playlists', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name,
                    description,
                    items: playlistItems
                })
            });
        }

        const result = await response.json();

        if (!result.success) {
            throw new Error(result.error);
        }

        closePlaylistModal();
        await loadPlaylists();

        showNotification(playlistId ? 'Playlist updated successfully' : 'Playlist created successfully', 'success');

    } catch (error) {
        console.error('Failed to save playlist:', error);
        showNotification('Failed to save playlist: ' + error.message, 'error');
    }
}

// ===== Playlist Actions =====

async function activatePlaylist(playlistId) {
    try {
        const response = await fetch(`/api/playlists/${playlistId}/activate`, {
            method: 'POST'
        });

        const result = await response.json();

        if (!result.success) {
            throw new Error(result.error);
        }

        await loadPlaylists();
        showNotification('Playlist activated successfully', 'success');

    } catch (error) {
        console.error('Failed to activate playlist:', error);
        showNotification('Failed to activate playlist: ' + error.message, 'error');
    }
}

async function deactivatePlaylist() {
    try {
        const response = await fetch('/api/playlists/deactivate', {
            method: 'POST'
        });

        const result = await response.json();

        if (!result.success) {
            throw new Error(result.error);
        }

        await loadPlaylists();
        showNotification('Playlist deactivated', 'success');

    } catch (error) {
        console.error('Failed to deactivate playlist:', error);
        showNotification('Failed to deactivate playlist: ' + error.message, 'error');
    }
}

async function deletePlaylist(playlistId, playlistName) {
    if (!confirm(`Are you sure you want to delete "${playlistName}"?`)) {
        return;
    }

    try {
        const response = await fetch(`/api/playlists/${playlistId}`, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (!result.success) {
            throw new Error(result.error);
        }

        await loadPlaylists();
        showNotification('Playlist deleted successfully', 'success');

    } catch (error) {
        console.error('Failed to delete playlist:', error);
        showNotification('Failed to delete playlist: ' + error.message, 'error');
    }
}

// ===== Utility Functions =====

function formatDuration(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    if (hours > 0) {
        return `${hours}h ${minutes}m`;
    } else if (minutes > 0) {
        return `${minutes}m ${secs}s`;
    } else {
        return `${secs}s`;
    }
}

function showNotification(message, type = 'info') {
    // Simple notification - could be enhanced with a proper toast system
    alert(message);
}
