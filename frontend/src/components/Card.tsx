import { ComponentChildren } from 'preact'
import clsx from 'clsx'
import styles from './Card.module.css'

interface CardProps {
  title?: string
  children: ComponentChildren
  class?: string
  actions?: ComponentChildren
}

export const Card = ({ title, children, class: className = '', actions }: CardProps) => (
  <div class={clsx(styles.card, className)}>
    {(title || actions) && (
      <div class={styles.header}>
        {title && <h2 class={styles.title}>{title}</h2>}
        {actions && <div class={styles.actions}>{actions}</div>}
      </div>
    )}
    {children}
  </div>
)
