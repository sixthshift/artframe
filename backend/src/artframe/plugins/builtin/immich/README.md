# Immich Album Sync Plugin

A pure Immich photo plugin that syncs album photos to local storage and displays them offline.

## Features

- **Full Album Sync**: Downloads all photos from an Immich album to local storage
- **Automatic Sync**: Periodically checks for changes and keeps photos in sync
- **Offline Operation**: Displays photos from local cache without API calls
- **Smart Updates**: Adds new photos and removes deleted ones automatically
- **Multiple Selection Modes**: Random, sequential, newest, or oldest
- **Configurable Limits**: Optionally limit maximum photos synced

## How It Works

1. **Initial Sync**: On first run, downloads all photos from the specified album
2. **Local Storage**: Photos stored in `~/.artframe/plugins/immich/{instance_id}/photos/`
3. **Periodic Sync**: Checks for changes based on sync interval (default: 6 hours)
4. **Display**: Shows photos from local cache (fast, no API calls)
5. **Auto-Cleanup**: Removes photos deleted from the server

## Configuration

### Required Settings

- **Immich Server URL**: Your Immich server address (e.g., `https://immich.example.com`)
- **Immich API Key**: API key from Immich user settings (Settings → Account → API Keys)

### Optional Settings

- **Album ID**: UUID of specific album (leave empty for all photos)
  - Find in Immich: Open album → Look at URL → Copy UUID
  - Example: `a1b2c3d4-e5f6-7890-abcd-ef1234567890`
- **Selection Mode**: How to select photos
  - `random` (default): Random photo each time
  - `sequential`: Cycle through photos in order
  - `newest`: Always show newest photo first
  - `oldest`: Always show oldest photo first
- **Sync Interval**: Hours between sync checks (default: 6, min: 1, max: 168)
- **Max Photos**: Limit number of synced photos (0 = unlimited)

## Getting Your API Key

1. Open Immich web interface
2. Go to **Settings** (gear icon)
3. Navigate to **Account Settings**
4. Scroll to **API Keys** section
5. Click **New API Key**
6. Give it a name (e.g., "Artframe")
7. Copy the generated key

## Getting Album ID

1. Open Immich web interface
2. Navigate to **Albums**
3. Open the album you want to display
4. Look at the URL in your browser:
   ```
   https://immich.example.com/albums/a1b2c3d4-e5f6-7890-abcd-ef1234567890
                                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                     This is your Album ID
   ```
5. Copy the UUID from the URL

## Usage Examples

### Example 1: Sync Specific Album

```json
{
  "immich_url": "https://immich.example.com",
  "immich_api_key": "your-api-key-here",
  "album_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "selection_mode": "random",
  "sync_interval_hours": 6
}
```

### Example 2: All Photos, Sequential Display

```json
{
  "immich_url": "https://immich.example.com",
  "immich_api_key": "your-api-key-here",
  "album_id": "",
  "selection_mode": "sequential",
  "sync_interval_hours": 12,
  "max_photos": 100
}
```

### Example 3: Latest Photo from Album

```json
{
  "immich_url": "https://immich.example.com",
  "immich_api_key": "your-api-key-here",
  "album_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "selection_mode": "newest",
  "sync_interval_hours": 1
}
```

## Storage

### Directory Structure

```
~/.artframe/plugins/immich/{instance_id}/
├── photos/                    # Synced photos
│   ├── IMG_1234.jpg
│   ├── IMG_1235.jpg
│   └── ...
└── sync_metadata.json         # Sync tracking data
```

### Metadata Format

```json
{
  "last_sync": "2025-10-12T10:30:00",
  "album_id": "uuid-of-album",
  "sync_count": 5,
  "synced_assets": {
    "asset-id-1": {
      "filename": "IMG_1234.jpg",
      "local_path": "IMG_1234.jpg",
      "file_created_at": "2025-01-15T12:00:00",
      "checksum": "md5-hash",
      "synced_at": "2025-10-12T10:30:00"
    }
  }
}
```

## Sync Behavior

### When Sync Happens

- First run (no local photos)
- Album ID changes
- Sync interval exceeded
- Manual request (force sync)

### What Gets Synced

- **Added**: New photos from server downloaded
- **Removed**: Photos deleted from server removed locally
- **Unchanged**: Existing photos skipped (uses checksum)

### Sync Performance

- **Initial sync** of 100 photos: ~2-5 minutes (depends on photo sizes)
- **Subsequent syncs**: Usually < 30 seconds (only changes)
- **Display time**: < 1 second (local file access)

## Advantages Over On-Demand Fetching

1. **Fast Display**: No API calls during display
2. **Offline Mode**: Works without internet after sync
3. **Reduced Load**: Fewer API requests to server
4. **Predictable**: Always know which photos are available
5. **Bandwidth**: Only downloads changes, not every photo

## Troubleshooting

### No Photos After Sync

- Check API key is valid
- Verify album ID is correct
- Ensure album contains photos (not videos)
- Check Immich server is accessible

### Sync Not Updating

- Check sync interval setting
- Verify last_sync time in metadata
- Try changing album_id to force re-sync
- Check network connectivity

### Storage Space Issues

- Set `max_photos` limit
- Manually clean `~/.artframe/plugins/immich/{instance_id}/photos/`
- Delete sync_metadata.json to reset

### Photos Not Displaying

- Check `~/.artframe/plugins/immich/{instance_id}/photos/` has files
- Verify file permissions
- Check plugin logs for errors

## API Endpoints Used

This plugin uses the following Immich API endpoints:

- `GET /api/albums/{id}?withoutAssets=false` - Get album with assets
- `POST /api/search/metadata` - Search all assets (when no album specified)
- `GET /api/assets/{id}/original` - Download full resolution photo

## Compatibility

- **Immich Version**: v1.106+
- **API Changes**: Plugin uses current stable endpoints as of 2025
- **Python**: 3.9+
- **Dependencies**: requests, Pillow

## Differences from immich_photos Plugin

| Feature | immich (this) | immich_photos |
|---------|---------------|---------------|
| AI Styling | ❌ No | ✅ Yes (NanoBanana) |
| Local Sync | ✅ Yes | ❌ No (on-demand) |
| Offline Mode | ✅ Yes | ❌ No |
| Sync Management | ✅ Yes | ❌ No |
| Album Support | ✅ Full | ⚠ Partial |
| Speed | ⚡ Fast | ⏱ Slower |

## Example Test

```bash
# Run the test script
python test_immich_plugin.py

# It will prompt for:
# - Immich server URL
# - API key
# - Album ID (optional)

# Test output saved to test_output/
```

## License

Same as Artframe project.
