import { Card } from '@/components'
import { Link } from 'wouter-preact'

export const Config = () => {
  return (
    <div class="max-w-4xl mx-auto">
      <div class="bg-blue-50 border-l-4 border-blue-500 p-4 mb-6 rounded">
        <p class="text-blue-800 mb-2">
          <strong>Configuration is managed via YAML files.</strong>
        </p>
        <p class="text-blue-700 mb-2">
          Edit the configuration files directly in{' '}
          <code class="bg-blue-100 px-1.5 py-0.5 rounded text-sm">config/artframe-laptop.yaml</code> (development) or{' '}
          <code class="bg-blue-100 px-1.5 py-0.5 rounded text-sm">config/artframe-pi.yaml</code> (production).
        </p>
        <p class="text-blue-700">
          Changes require a restart of the Artframe service to take effect.
        </p>
      </div>

      <div class="flex flex-col gap-6">
        <Card title="Configuration Overview">
          <div class="bg-gray-50 p-5 rounded-lg border-l-4 border-primary-500 mb-5">
            <h3 class="text-primary-500 font-semibold mb-3">Schedule Settings</h3>
            <p class="text-gray-600 mb-3">
              Configure update times and timezone in the <code class="bg-gray-200 px-1.5 py-0.5 rounded text-sm">schedule</code> section of
              your config file.
            </p>
            <pre class="config-example">
{`artframe:
  schedule:
    update_time: "06:00"
    timezone: "Australia/Sydney"`}
            </pre>
          </div>

          <div class="bg-gray-50 p-5 rounded-lg border-l-4 border-primary-500 mb-5">
            <h3 class="text-primary-500 font-semibold mb-3">Display Settings</h3>
            <p class="text-gray-600 mb-3">
              Configure display driver and dimensions in the <code class="bg-gray-200 px-1.5 py-0.5 rounded text-sm">display</code> section.
            </p>
            <pre class="config-example">
{`artframe:
  display:
    driver: "mock"  # or "waveshare"
    config:
      width: 600
      height: 448
      save_images: true`}
            </pre>
          </div>

          <div class="bg-gray-50 p-5 rounded-lg border-l-4 border-primary-500">
            <h3 class="text-primary-500 font-semibold mb-3">Storage & Cache</h3>
            <p class="text-gray-600 mb-3">
              Configure storage directories and cache limits.
            </p>
            <pre class="config-example">
{`artframe:
  storage:
    directory: "./data/storage"
  cache:
    cache_directory: "./data/cache"
    max_size_mb: 500
    retention_days: 30`}
            </pre>
          </div>
        </Card>

        <Card title="Plugin Configuration">
          <p class="text-gray-600">
            Plugin instances are configured through the{' '}
            <Link href="/plugins" class="text-primary-500 hover:underline font-medium">Plugins page</Link>. Each instance stores its settings
            in <code class="bg-gray-200 px-1.5 py-0.5 rounded text-sm">~/.artframe/data/plugin_instances.json</code>.
          </p>
        </Card>

        <Card title="Environment Variables">
          <p class="text-gray-600 mb-4">
            Sensitive configuration (API keys, credentials) should be stored in
            environment variables or a <code class="bg-gray-200 px-1.5 py-0.5 rounded text-sm">.env</code> file.
          </p>
          <div class="overflow-x-auto">
            <table class="w-full border-collapse">
              <thead>
                <tr class="bg-gray-50">
                  <th class="p-3 text-left font-semibold border-b border-gray-200">Variable</th>
                  <th class="p-3 text-left font-semibold border-b border-gray-200">Description</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td class="p-3 border-b border-gray-100">
                    <code class="bg-gray-100 px-2 py-0.5 rounded font-mono text-sm">ARTFRAME_CONFIG</code>
                  </td>
                  <td class="p-3 border-b border-gray-100 text-gray-600">Path to config file (auto-detected if not set)</td>
                </tr>
                <tr>
                  <td class="p-3 border-b border-gray-100">
                    <code class="bg-gray-100 px-2 py-0.5 rounded font-mono text-sm">IMMICH_API_KEY</code>
                  </td>
                  <td class="p-3 border-b border-gray-100 text-gray-600">API key for Immich server (if using Immich plugin)</td>
                </tr>
                <tr>
                  <td class="p-3">
                    <code class="bg-gray-100 px-2 py-0.5 rounded font-mono text-sm">IMMICH_URL</code>
                  </td>
                  <td class="p-3 text-gray-600">URL to Immich server</td>
                </tr>
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    </div>
  )
}
