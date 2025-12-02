import { ComponentChildren } from 'preact'
import clsx from 'clsx'
import styles from './Button.module.css'

type ButtonVariant = 'primary' | 'secondary' | 'warning' | 'danger' | 'success'
type ButtonSize = 'normal' | 'small'

interface ButtonProps {
  children: ComponentChildren
  variant?: ButtonVariant
  size?: ButtonSize
  disabled?: boolean
  loading?: boolean
  onClick?: () => void
  type?: 'button' | 'submit' | 'reset'
  class?: string
}

export const Button = ({
  children,
  variant = 'primary',
  size = 'normal',
  disabled = false,
  loading = false,
  onClick,
  type = 'button',
  class: className = '',
}: ButtonProps) => (
  <button
    type={type}
    class={clsx(
      styles.btn,
      styles[variant],
      size === 'small' && styles.small,
      className
    )}
    disabled={disabled || loading}
    onClick={onClick}
  >
    {loading ? '⏳ Loading...' : children}
  </button>
)
