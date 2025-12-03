import clsx from 'clsx'
import { Card, Button, StatusGrid, StatusItem, showToast } from '@/components'
import {
  useSystemStatus,
  useConnections,
  useSchedulerStatus,
  useCurrentDisplay,
  useToggleScheduler,
  useTriggerUpdate,
  useClearDisplay,
} from '@/queries'
import styles from './Dashboard.module.css'
import { formatTimestamp } from './Dashboard.utils'

export const Dashboard = () => {
  const { data: status, isLoading: statusLoading } = useSystemStatus()
  const { data: connections, isLoading: connectionsLoading } = useConnections()
  const { data: scheduler } = useSchedulerStatus()
  const { data: display, isLoading: displayLoading } = useCurrentDisplay()

  const toggleScheduler = useToggleScheduler()
  const triggerUpdate = useTriggerUpdate()
  const clearDisplay = useClearDisplay()

  const handleToggleScheduler = async () => {
    try {
      await toggleScheduler.mutateAsync(scheduler?.paused ? false : true)
      showToast(
        scheduler?.paused ? 'Scheduler resumed' : 'Scheduler paused',
        'success'
      )
    } catch {
      showToast('Failed to toggle scheduler', 'error')
    }
  }

  const handleTriggerUpdate = async () => {
    try {
      await triggerUpdate.mutateAsync()
      showToast('Update completed successfully', 'success')
    } catch {
      showToast('Update failed', 'error')
    }
  }

  const handleClearDisplay = async () => {
    if (!confirm('Are you sure you want to clear the display?')) return
    try {
      await clearDisplay.mutateAsync()
      showToast('Display cleared', 'success')
    } catch {
      showToast('Failed to clear display', 'error')
    }
  }

  return (
    <div>
      {/* Controls */}
      <div class={styles.controls}>
        <Button
          variant="primary"
          onClick={handleTriggerUpdate}
          loading={triggerUpdate.isPending}
        >
          🔄 Update Now
        </Button>
        <Button
          variant="secondary"
          onClick={handleClearDisplay}
          loading={clearDisplay.isPending}
        >
          🗑️ Clear Display
        </Button>
        <Button
          variant={scheduler?.paused ? 'success' : 'warning'}
          onClick={handleToggleScheduler}
          loading={toggleScheduler.isPending}
        >
          {scheduler?.paused ? '▶️ Resume Scheduler' : '⏸️ Pause Scheduler'}
        </Button>
      </div>

      {/* Scheduler Status Bar */}
      <div class={styles.schedulerBar}>
        {scheduler && (
          <div class={styles.schedulerInfo}>
            <span>
              <strong>Scheduler:</strong>{' '}
              <span class={clsx(styles.badge, scheduler.paused ? styles.warning : styles.success)}>
                {scheduler.paused ? 'PAUSED' : 'ACTIVE'}
              </span>
            </span>
            <span>
              <strong>Next Update:</strong>{' '}
              {scheduler.next_update ? new Date(scheduler.next_update).toLocaleString() : 'N/A'}
            </span>
            {scheduler.paused && (
              <span class={styles.pausedNote}>
                ⚡ Daily e-ink refresh still active for screen health
              </span>
            )}
          </div>
        )}
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column: Display Preview */}
        <div>
          <Card title="Current Display">
            {displayLoading ? (
              <p class="text-gray-500 italic text-center py-4">Loading current display...</p>
            ) : display?.has_preview ? (
              <div class={styles.displayPreview}>
                <img
                  src={`/api/display/preview?t=${Date.now()}`}
                  alt="Current Display"
                  onError={(e) => {
                    ;(e.target as HTMLImageElement).style.display = 'none'
                  }}
                />
              </div>
            ) : (
              <div class={styles.displayPlaceholder}>
                <div class={styles.icon}>🖼️</div>
                <h3>Physical E-ink Display</h3>
                <p>
                  Enable save_images in driver config for preview
                </p>
              </div>
            )}

            {display && (
              <div class={styles.displayInfo}>
                <div class={styles.displayInfoItem}>
                  <span class={styles.label}>Plugin</span>
                  <span class={styles.value}>{display.plugin_name || 'N/A'}</span>
                </div>
                <div class={styles.displayInfoItem}>
                  <span class={styles.label}>Instance</span>
                  <span class={styles.value}>{display.instance_name || 'N/A'}</span>
                </div>
                <div class={styles.displayInfoItem}>
                  <span class={styles.label}>Last Updated</span>
                  <span class={styles.value}>{formatTimestamp(display.last_update)}</span>
                </div>
                <div class={styles.displayInfoItem}>
                  <span class={styles.label}>Status</span>
                  <span class={clsx(styles.value, display.status === 'ready' && 'text-emerald-600')}>
                    {display.status}
                  </span>
                </div>
              </div>
            )}
          </Card>
        </div>

        {/* Right Column: Status Cards */}
        <div class="flex flex-col gap-6">
          {/* System Status */}
          <Card title="System Status">
            {statusLoading ? (
              <p class="text-gray-500 italic text-center py-4">Loading...</p>
            ) : status ? (
              <StatusGrid>
                <StatusItem
                  label="Running"
                  value={status.running ? '✓ Yes' : '✗ No'}
                  status={status.running ? 'success' : 'error'}
                />
                <StatusItem
                  label="Last Update"
                  value={formatTimestamp(status.last_update)}
                />
                <StatusItem
                  label="Next Scheduled"
                  value={status.next_scheduled || 'N/A'}
                />
                <StatusItem
                  label="Cache Images"
                  value={status.cache_stats?.total_images ?? 'N/A'}
                />
                <StatusItem
                  label="Cache Size"
                  value={status.cache_stats ? `${status.cache_stats.total_size_mb} MB` : 'N/A'}
                />
                <StatusItem
                  label="Display Status"
                  value={status.display_state?.status ?? status.display_status ?? 'Unknown'}
                />
                <StatusItem
                  label="Display Errors"
                  value={status.display_state?.error_count ?? 0}
                  status={(status.display_state?.error_count ?? 0) > 0 ? 'error' : 'success'}
                />
              </StatusGrid>
            ) : (
              <p class="text-red-500 p-4 bg-red-50 rounded">Failed to load status</p>
            )}
          </Card>

          {/* Connections */}
          <Card title="Connections">
            {connectionsLoading ? (
              <p class="text-gray-500 italic text-center py-4">Loading...</p>
            ) : connections ? (
              <div class="grid gap-3">
                {Object.entries(connections).map(([service, connected]) => (
                  <div key={service} class="flex justify-between p-3 bg-gray-50 rounded">
                    <span class="font-semibold text-gray-600">
                      {service.charAt(0).toUpperCase() + service.slice(1)}:
                    </span>
                    <span class={clsx('font-mono font-semibold', connected ? 'text-emerald-600' : 'text-red-600')}>
                      {connected ? '✓ Connected' : '✗ Failed'}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p class="text-red-500 p-4 bg-red-50 rounded">Failed to load connections</p>
            )}
          </Card>
        </div>
      </div>
    </div>
  )
}
