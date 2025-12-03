import { Card } from '@/components'
import { Link } from 'wouter-preact'
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
  description,
  children,
}: {
  icon: string
  title: string
  description: string
  children: preact.ComponentChildren
}) => (
  <div class={styles.section}>
    <div class={styles.sectionHeader}>
      <span class={styles.sectionIcon}>{icon}</span>
      <div>
        <h3 class={styles.sectionTitle}>{title}</h3>
        <p class={styles.sectionDescription}>{description}</p>
      </div>
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
        <Card title="Configuration Reference">
          <div class={styles.sectionsGrid}>
            <ConfigSection
              icon="🕐"
              title="Schedule"
              description="Configure when the display updates"
            >
              <ConfigItem label="Update Time" value="06:00" hint="24-hour format" />
              <ConfigItem label="Timezone" value="Australia/Sydney" hint="IANA timezone" />
            </ConfigSection>

            <ConfigSection
              icon="🖥️"
              title="Display"
              description="Set the display driver and dimensions"
            >
              <ConfigItem label="Driver" value="mock" hint="mock or waveshare" />
              <ConfigItem label="Width" value="600" hint="pixels" />
              <ConfigItem label="Height" value="448" hint="pixels" />
              <ConfigItem label="Save Images" value="true" hint="enables preview" />
            </ConfigSection>

            <ConfigSection
              icon="💾"
              title="Storage & Cache"
              description="Configure directories and limits"
            >
              <ConfigItem label="Storage Directory" value="./data/storage" />
              <ConfigItem label="Cache Directory" value="./data/cache" />
              <ConfigItem label="Max Cache Size" value="500" hint="MB" />
              <ConfigItem label="Retention" value="30" hint="days" />
            </ConfigSection>
          </div>
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
