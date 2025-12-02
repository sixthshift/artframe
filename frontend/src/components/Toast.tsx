import { signal } from '@preact/signals'
import clsx from 'clsx'
import styles from './Toast.module.css'

interface ToastMessage {
  id: number
  message: string
  type: 'success' | 'error' | 'info' | 'warning'
}

// Global toast state using Preact signals
const toasts = signal<ToastMessage[]>([])
let toastId = 0

export function showToast(
  message: string,
  type: 'success' | 'error' | 'info' | 'warning' = 'info'
) {
  const id = ++toastId
  toasts.value = [...toasts.value, { id, message, type }]

  setTimeout(() => {
    toasts.value = toasts.value.filter((t) => t.id !== id)
  }, 3000)
}

export const ToastContainer = () => (
  <div class={styles.container}>
    {toasts.value.map((toast) => (
      <div
        key={toast.id}
        class={clsx(styles.toast, styles[toast.type])}
      >
        {toast.message}
      </div>
    ))}
  </div>
)
