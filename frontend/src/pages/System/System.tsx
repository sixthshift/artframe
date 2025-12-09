import { useState } from 'preact/hooks'
import { Card, Button, StatusGrid, StatusItem } from '@/components'
import {
  useSystemInfo,
  useDisplayHealth,
  useLogs,
  useHardwareTest,
} from '@/queries'
import { formatDateTime } from '@/utils/date'

export const System = () => {
  const { data: systemInfo, isLoading: systemLoading } = useSystemInfo()
  const { data: displayHealth, isLoading: healthLoading } = useDisplayHealth()
  const [logLevel, setLogLevel] = useState<string>('')
  const { data: logs = [], refetch: refetchLogs } = useLogs(logLevel || undefined)
  const hardwareTest = useHardwareTest()
  const [testResult, setTestResult] = useState<string | null>(null)

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

  const handleHardwareTest = () => {
    setTestResult(null)
    hardwareTest.mutate(undefined, {
      onSuccess: (data) => {
        setTestResult(data.message)
      },
      onError: (error) => {
        setTestResult(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`)
      },
    })
  }

  return (
    <div class="max-w-7xl mx-auto">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        {/* System Info */}
        <Card title="System Information">
          {systemLoading ? (
            <p class="text-gray-500 italic text-center py-4">Loading...</p>
          ) : systemInfo ? (
            <StatusGrid>
              <StatusItem label="CPU Usage" value={`${systemInfo.cpu_percent || 'N/A'}%`} />
              <StatusItem label="Memory" value={`${systemInfo.memory_percent || 'N/A'}%`} />
              <StatusItem label="Temperature" value={`${systemInfo.temperature || 'N/A'}°C`} />
              <StatusItem label="Disk Usage" value={`${systemInfo.disk_percent || 'N/A'}%`} />
              <StatusItem label="Uptime" value={systemInfo.uptime || 'N/A'} />
              <StatusItem label="Platform" value={systemInfo.platform || 'N/A'} />
            </StatusGrid>
          ) : (
            <p class="text-red-500 p-4 bg-red-50 rounded">Failed to load system info</p>
          )}
        </Card>

        {/* E-ink Health */}
        <Card title="E-ink Display Health">
          {healthLoading ? (
            <p class="text-gray-500 italic text-center py-4">Loading...</p>
          ) : displayHealth ? (
            <>
              <StatusGrid>
                <StatusItem label="Total Refreshes" value={displayHealth.refresh_count || 0} />
                <StatusItem label="Last Refresh" value={formatDateTime(displayHealth.last_refresh) || 'Never'} />
              </StatusGrid>
              <div class="mt-4 pt-4 border-t border-gray-200">
                <div class="flex items-center justify-between">
                  <div>
                    <p class="text-sm font-medium text-gray-700">Hardware Test</p>
                    <p class="text-xs text-gray-500">Display test pattern to verify connectivity</p>
                  </div>
                  <Button
                    size="small"
                    variant="secondary"
                    onClick={handleHardwareTest}
                    disabled={hardwareTest.isPending}
                  >
                    {hardwareTest.isPending ? 'Testing...' : 'Run Test'}
                  </Button>
                </div>
                {testResult && (
                  <p class={`mt-2 text-sm ${testResult.startsWith('Error') ? 'text-red-600' : 'text-green-600'}`}>
                    {testResult}
                  </p>
                )}
              </div>
            </>
          ) : (
            <p class="text-red-500 p-4 bg-red-50 rounded">Failed to load e-ink health</p>
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
