import { Card } from '@/components'
import { Link } from 'wouter-preact'
import { useConfig } from '@/queries'
import styles from './Config.module.css'

const ConfigItem = ({ label, value, hint }: { label: string; value: string; hint?: string }) => (
  <div class={styles.configItem}>
    <span class={styles.configLabel}>{label}</span>
    <div class={styles.configValueWrapper}>
      <span class={styles.configValue}>{value}</span>
      {hint && <span class={styles.configLabel}>{hint}</span>}
    </div>
  </div>
)

const ConfigSection = ({
  icon,
  title,
  children,
}: {
  icon: string
  title: string
  children: preact.ComponentChildren
}) => (
  <div class={styles.section}>
    <div class={styles.sectionHeader}>
      <span class={styles.sectionIcon}>{icon}</span>
      <h3 class={styles.sectionTitle}>{title}</h3>
    </div>
    <div class={styles.configItems}>{children}</div>
  </div>
)

const EnvRow = ({ name, description }: { name: string; description: string }) => (
  <div class={styles.envRow}>
    <code class={styles.envName}>{name}</code>
    <span class={styles.envDescription}>{description}</span>
  </div>
)

export const Config = () => {
  const { data: config, isLoading } = useConfig()

  const artframe = config?.artframe
  const display = artframe?.display
  const displayConfig = display?.config
  const scheduler = artframe?.scheduler
  const storage = artframe?.storage
  const web = artframe?.web
  const logging = artframe?.logging

  // Check if sections have any content
  const hasScheduler = scheduler && (scheduler.timezone || scheduler.update_times?.length)
  const hasDisplay = display && (display.driver || displayConfig)
  const hasStorage = storage && (storage.data_dir || storage.cache_dir)
  const hasWeb = web && (web.host || web.port)
  const hasLogging = logging && (logging.level || logging.dir)

  return (
    <div class="max-w-4xl mx-auto">
      {/* Info Banner */}
      <div class={styles.banner}>
        <div class={styles.bannerIcon}>📝</div>
        <div class={styles.bannerContent}>
          <p class={styles.bannerTitle}>Configuration is managed via YAML files</p>
          <p class={styles.bannerText}>
            Edit <code class={styles.inlineCode}>config/artframe-laptop.yaml</code> (development) or{' '}
            <code class={styles.inlineCode}>config/artframe-pi.yaml</code> (production).
            Changes require a service restart to take effect.
          </p>
        </div>
      </div>

      <div class="flex flex-col gap-6">
        {/* Main Configuration */}
        <Card title="Current Configuration">
          {isLoading ? (
            <p class="text-gray-500 italic text-center py-4">Loading configuration...</p>
          ) : (
            <div class={styles.sectionsGrid}>
              {hasScheduler && (
                <ConfigSection icon="🕐" title="Scheduler">
                  {scheduler.timezone && (
                    <ConfigItem label="Timezone" value={scheduler.timezone} hint="timezone" />
                  )}
                  {scheduler.update_times && scheduler.update_times.length > 0 && (
                    <ConfigItem
                      label="Update Times"
                      value={scheduler.update_times.join(', ')}
                      hint="24-hour format"
                    />
                  )}
                </ConfigSection>
              )}

              {hasDisplay && (
                <ConfigSection icon="🖥️" title="Display">
                  {display.driver && <ConfigItem label="Driver" value={display.driver} />}
                  {displayConfig?.width != null && (
                    <ConfigItem label="Width" value={String(displayConfig.width)} hint="pixels" />
                  )}
                  {displayConfig?.height != null && (
                    <ConfigItem label="Height" value={String(displayConfig.height)} hint="pixels" />
                  )}
                  {displayConfig?.save_images != null && (
                    <ConfigItem
                      label="Save Images"
                      value={String(displayConfig.save_images)}
                      hint="enables preview"
                    />
                  )}
                </ConfigSection>
              )}

              {hasStorage && (
                <ConfigSection icon="💾" title="Storage">
                  {storage.data_dir && <ConfigItem label="Data Directory" value={storage.data_dir} />}
                  {storage.cache_dir && <ConfigItem label="Cache Directory" value={storage.cache_dir} />}
                </ConfigSection>
              )}

              {hasWeb && (
                <ConfigSection icon="🌐" title="Web Server">
                  {web.host && <ConfigItem label="Host" value={web.host} />}
                  {web.port != null && <ConfigItem label="Port" value={String(web.port)} />}
                </ConfigSection>
              )}

              {hasLogging && (
                <ConfigSection icon="📋" title="Logging">
                  {logging.level && <ConfigItem label="Level" value={logging.level} />}
                  {logging.dir && <ConfigItem label="Directory" value={logging.dir} />}
                </ConfigSection>
              )}

              {!hasScheduler && !hasDisplay && !hasStorage && !hasWeb && !hasLogging && (
                <p class="text-gray-500 italic text-center py-4">No configuration found</p>
              )}
            </div>
          )}
        </Card>

        {/* Plugin Configuration */}
        <Card title="Plugin Configuration">
          <div class={styles.pluginInfo}>
            <div class={styles.pluginIcon}>🧩</div>
            <div class={styles.pluginContent}>
              <p class={styles.pluginText}>
                Plugin instances are configured through the{' '}
                <Link href="/plugins" class={styles.link}>
                  Plugins page
                </Link>
                . Each instance stores its settings in:
              </p>
              <code class={styles.pathCode}>~/.artframe/data/plugin_instances.json</code>
            </div>
          </div>
        </Card>

        {/* Environment Variables */}
        <Card title="Environment Variables">
          <p class={styles.envIntro}>
            Sensitive configuration (API keys, credentials) should be stored in environment variables
            or a <code class={styles.inlineCode}>.env</code> file.
          </p>
          <div class={styles.envList}>
            <EnvRow
              name="ARTFRAME_CONFIG"
              description="Path to config file (auto-detected if not set)"
            />
            <EnvRow
              name="IMMICH_API_KEY"
              description="API key for Immich server (if using Immich plugin)"
            />
            <EnvRow
              name="IMMICH_URL"
              description="URL to Immich server"
            />
          </div>
        </Card>
      </div>
    </div>
  )
}
