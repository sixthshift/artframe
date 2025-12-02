import { ComponentChildren } from 'preact'
import clsx from 'clsx'
import styles from './StatusGrid.module.css'

interface StatusItemProps {
  label: string
  value: ComponentChildren
  status?: 'success' | 'error' | 'warning' | 'normal'
}

export const StatusItem = ({ label, value, status = 'normal' }: StatusItemProps) => {
  return (
    <div class={styles.statusItem}>
      <span class={styles.statusLabel}>{label}:</span>
      <span class={clsx(styles.statusValue, styles[status])}>{value}</span>
    </div>
  )
}

interface StatusGridProps {
  children: ComponentChildren
}

export const StatusGrid = ({ children }: StatusGridProps) => {
  return <div class={styles.statusGrid}>{children}</div>
}

interface InfoGridProps {
  children: ComponentChildren
}

export const InfoGrid = ({ children }: InfoGridProps) => {
  return <div class={styles.infoGrid}>{children}</div>
}

interface InfoItemProps {
  label: string
  value: ComponentChildren
  status?: 'success' | 'error' | 'warning' | 'normal'
}

export const InfoItem = ({ label, value, status = 'normal' }: InfoItemProps) => {
  return (
    <div class={styles.infoItem}>
      <span class={styles.infoLabel}>{label}</span>
      <span class={clsx(styles.infoValue, styles[status])}>
        {value}
      </span>
    </div>
  )
}
