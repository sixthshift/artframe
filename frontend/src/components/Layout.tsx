import { ComponentChildren } from 'preact'
import { Link, useLocation } from 'wouter-preact'
import clsx from 'clsx'
import { ToastContainer } from './Toast'
import styles from './Layout.module.css'

interface LayoutProps {
  children: ComponentChildren
}

const navItems = [
  { path: '/', label: 'Dashboard', icon: '📊' },
  { path: '/plugins', label: 'Plugins', icon: '🔌' },
  { path: '/schedule', label: 'Schedule', icon: '📅' },
  { path: '/system', label: 'System', icon: '📈' },
  { path: '/config', label: 'Config', icon: '⚙️' },
]

export const Layout = ({ children }: LayoutProps) => {
  const [location] = useLocation()

  return (
    <div class={styles.layout}>
      <header class={styles.header}>
        <div class={styles.headerContent}>
          <div class={styles.headerTop}>
            <Link href="/" class={styles.branding}>
              <h1>🖼️ Artframe</h1>
              <p>Digital Photo Frame Dashboard</p>
            </Link>
            <nav class={styles.nav}>
              {navItems.map((item) => (
                <Link
                  key={item.path}
                  href={item.path}
                  class={clsx(styles.navTab, location === item.path && styles.active)}
                >
                  {item.icon} {item.label}
                </Link>
              ))}
            </nav>
          </div>
        </div>
      </header>

      <main class={styles.main}>{children}</main>

      <footer class={styles.footer}>
        <p>&copy; 2025 Artframe</p>
      </footer>

      <ToastContainer />
    </div>
  )
}
