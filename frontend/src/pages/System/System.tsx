import { useState } from 'preact/hooks'
import { Card, Button, InfoGrid, InfoItem } from '@/components'
import {
  useSystemInfo,
  useDisplayHealth,
  useSystemStatus,
  useLogs,
} from '@/queries'
import { formatDateTime } from '@/utils/date'

export const System = () => {
  const { data: systemInfo, isLoading: systemLoading } = useSystemInfo()
  const { data: displayHealth, isLoading: healthLoading } = useDisplayHealth()
  const { data: status, isLoading: statusLoading } = useSystemStatus()
  const [logLevel, setLogLevel] = useState<string>('')
  const { data: logs = [], refetch: refetchLogs } = useLogs(logLevel || undefined)

  const handleExportLogs = async () => {
    try {
      const response = await fetch('/api/system/logs/export')
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `artframe-logs-${new Date().toISOString()}.txt`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
    } catch {
      alert('Failed to export logs')
    }
  }

  return (
    <div class="max-w-7xl mx-auto">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-6">
        {/* System Info */}
        <Card title="System Information">
          {systemLoading ? (
            <p class="text-gray-500 italic text-center py-4">Loading...</p>
          ) : systemInfo ? (
            <InfoGrid>
              <InfoItem label="CPU Usage" value={`${systemInfo.cpu_percent || 'N/A'}%`} />
              <InfoItem label="Memory" value={`${systemInfo.memory_percent || 'N/A'}%`} />
              <InfoItem label="Temperature" value={`${systemInfo.temperature || 'N/A'}°C`} />
              <InfoItem label="Disk Usage" value={`${systemInfo.disk_percent || 'N/A'}%`} />
              <InfoItem label="Uptime" value={systemInfo.uptime || 'N/A'} />
              <InfoItem label="Platform" value={systemInfo.platform || 'N/A'} />
            </InfoGrid>
          ) : (
            <p class="text-red-500 p-4 bg-red-50 rounded">Failed to load system info</p>
          )}
        </Card>

        {/* E-ink Health */}
        <Card title="E-ink Display Health">
          {healthLoading ? (
            <p class="text-gray-500 italic text-center py-4">Loading...</p>
          ) : displayHealth ? (
            <InfoGrid>
              <InfoItem label="Total Refreshes" value={displayHealth.refresh_count || 0} />
              <InfoItem label="Last Refresh" value={formatDateTime(displayHealth.last_refresh) || 'Never'} />
              <InfoItem
                label="Status"
                value={displayHealth.status || 'Unknown'}
                status={displayHealth.status === 'ready' ? 'success' : 'normal'}
              />
              <InfoItem
                label="Error Count"
                value={displayHealth.error_count || 0}
                status={displayHealth.error_count > 0 ? 'error' : 'success'}
              />
            </InfoGrid>
          ) : (
            <p class="text-red-500 p-4 bg-red-50 rounded">Failed to load e-ink health</p>
          )}
        </Card>

        {/* Cache Stats */}
        <Card title="Cache Statistics">
          {statusLoading ? (
            <p class="text-gray-500 italic text-center py-4">Loading...</p>
          ) : status ? (
            <InfoGrid>
              <InfoItem label="Total Images" value={status.cache_stats?.total_images ?? 0} />
              <InfoItem label="Cache Size" value={`${status.cache_stats?.total_size_mb ?? 0} MB`} />
              <InfoItem label="Oldest Image" value={status.cache_stats?.oldest_image ?? 'N/A'} />
              <InfoItem label="Newest Image" value={status.cache_stats?.newest_image ?? 'N/A'} />
            </InfoGrid>
          ) : (
            <p class="text-red-500 p-4 bg-red-50 rounded">Failed to load cache stats</p>
          )}
        </Card>
      </div>

      {/* Logs */}
      <Card
        title="System Logs"
        actions={
          <div class="flex gap-2 items-center">
            <select
              class="select max-w-[150px]"
              value={logLevel}
              onChange={(e) => setLogLevel((e.target as HTMLSelectElement).value)}
            >
              <option value="">All Levels</option>
              <option value="DEBUG">Debug</option>
              <option value="INFO">Info</option>
              <option value="WARNING">Warning</option>
              <option value="ERROR">Error</option>
            </select>
            <Button size="small" variant="secondary" onClick={() => refetchLogs()}>
              Refresh
            </Button>
            <Button size="small" variant="secondary" onClick={handleExportLogs}>
              Export
            </Button>
          </div>
        }
      >
        <div class="logs-container">
          {logs.length === 0 ? (
            <p class="text-gray-400 text-center py-8">No logs available</p>
          ) : (
            logs.map((log, i) => (
              <div key={i} class={`log-entry log-${log.level.toLowerCase()}`}>
                <span class="log-time">{log.timestamp}</span>
                <span class="log-level">{log.level}</span>
                <span class="log-message">{log.message}</span>
              </div>
            ))
          )}
        </div>
      </Card>
    </div>
  )
}
