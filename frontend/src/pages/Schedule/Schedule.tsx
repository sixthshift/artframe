import { useState, useEffect, useCallback } from 'preact/hooks'
import clsx from 'clsx'
import { Button, showToast } from '@/components'
import {
  useSchedules,
  useCurrentSchedule,
  useSetSlot,
  useBulkSetSlots,
  useClearSlot,
  useClearAllSlots,
} from '@/queries'
import { useInstances, usePlaylists } from '@/queries'
import type { ScheduleSlots } from '@/api/types'
import styles from './Schedule.module.css'
import { DAY_NAMES, getColorForId, getCurrentDayIndex } from './Schedule.utils'

export const Schedule = () => {
  const { data: scheduleData, isLoading } = useSchedules()
  const { data: currentStatus } = useCurrentSchedule()
  const { data: instances = [] } = useInstances()
  const { data: playlists = [] } = usePlaylists()

  const [selectedSlots, setSelectedSlots] = useState<Set<string>>(new Set())
  const [isSelecting, setIsSelecting] = useState(false)
  const [selectionStart, setSelectionStart] = useState<{ day: number; hour: number } | null>(null)
  const [slotModalOpen, setSlotModalOpen] = useState(false)
  const [slotModalData, setSlotModalData] = useState<{ day: number; hour: number; existing?: { target_type: string; target_id: string } } | null>(null)
  const [bulkModalOpen, setBulkModalOpen] = useState(false)

  const setSlot = useSetSlot()
  const bulkSetSlots = useBulkSetSlots()
  const clearSlot = useClearSlot()
  const clearAllSlots = useClearAllSlots()

  const slots: ScheduleSlots = scheduleData?.slots || {}
  const enabledInstances = instances.filter((i) => i.enabled)
  const enabledPlaylists = playlists.filter((p) => p.enabled)

  const getSlotInfo = (slot: { target_type: string; target_id: string }) => {
    if (slot.target_type === 'playlist') {
      const playlist = enabledPlaylists.find((p) => p.id === slot.target_id)
      return { name: playlist?.name || 'Unknown', icon: '📋' }
    }
    const instance = enabledInstances.find((i) => i.id === slot.target_id)
    return { name: instance?.name || 'Unknown', icon: '📷' }
  }

  const onSlotMouseDown = (e: MouseEvent, day: number, hour: number) => {
    e.preventDefault()
    const slotKey = `${day}-${hour}`

    if (e.shiftKey && selectionStart) {
      extendSelection(day, hour)
    } else if (e.ctrlKey || e.metaKey) {
      setSelectedSlots((prev) => {
        const next = new Set(prev)
        if (next.has(slotKey)) {
          next.delete(slotKey)
        } else {
          next.add(slotKey)
        }
        return next
      })
      setSelectionStart({ day, hour })
    } else {
      setSelectedSlots(new Set([slotKey]))
      setSelectionStart({ day, hour })
      setIsSelecting(true)
    }
  }

  const onSlotMouseEnter = (day: number, hour: number) => {
    if (!isSelecting) return
    extendSelection(day, hour)
  }

  const extendSelection = (endDay: number, endHour: number) => {
    if (!selectionStart) return

    const minDay = Math.min(selectionStart.day, endDay)
    const maxDay = Math.max(selectionStart.day, endDay)
    const minHour = Math.min(selectionStart.hour, endHour)
    const maxHour = Math.max(selectionStart.hour, endHour)

    const newSelection = new Set<string>()
    for (let d = minDay; d <= maxDay; d++) {
      for (let h = minHour; h <= maxHour; h++) {
        newSelection.add(`${d}-${h}`)
      }
    }
    setSelectedSlots(newSelection)
  }

  const onMouseUp = useCallback(() => {
    if (isSelecting) {
      setIsSelecting(false)
      if (selectedSlots.size === 1) {
        const slotKey = [...selectedSlots][0]
        const [d, h] = slotKey.split('-').map(Number)
        setSelectedSlots(new Set())
        setSlotModalData({
          day: d,
          hour: h,
          existing: slots[slotKey],
        })
        setSlotModalOpen(true)
      }
    }
  }, [isSelecting, selectedSlots, slots])

  useEffect(() => {
    document.addEventListener('mouseup', onMouseUp)
    return () => document.removeEventListener('mouseup', onMouseUp)
  }, [onMouseUp])

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setSelectedSlots(new Set())
        setSelectionStart(null)
      }
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [])

  const handleSaveSlot = async (targetValue: string) => {
    if (!slotModalData) return

    try {
      if (!targetValue) {
        await clearSlot.mutateAsync({ day: slotModalData.day, hour: slotModalData.hour })
      } else {
        const [targetType, targetId] = targetValue.split(':')
        await setSlot.mutateAsync({
          day: slotModalData.day,
          hour: slotModalData.hour,
          target_type: targetType as 'instance' | 'playlist',
          target_id: targetId,
        })
      }
      showToast('Slot updated', 'success')
      setSlotModalOpen(false)
    } catch {
      showToast('Failed to save slot', 'error')
    }
  }

  const handleBulkAssign = async (targetValue: string) => {
    if (!targetValue || selectedSlots.size === 0) {
      showToast('Please select content to assign', 'error')
      return
    }

    const [targetType, targetId] = targetValue.split(':')
    const slotsArray = [...selectedSlots].map((key) => {
      const [day, hour] = key.split('-').map(Number)
      return { day, hour, target_type: targetType as 'instance' | 'playlist', target_id: targetId }
    })

    try {
      await bulkSetSlots.mutateAsync({ slots: slotsArray })
      showToast(`Assigned content to ${slotsArray.length} slots`, 'success')
      setBulkModalOpen(false)
      setSelectedSlots(new Set())
    } catch {
      showToast('Failed to assign slots', 'error')
    }
  }

  const handleClearSelected = async () => {
    if (selectedSlots.size === 0) return
    if (!confirm(`Clear ${selectedSlots.size} selected slots?`)) return

    try {
      for (const key of selectedSlots) {
        const [day, hour] = key.split('-').map(Number)
        await clearSlot.mutateAsync({ day, hour })
      }
      setSelectedSlots(new Set())
      showToast('Selected slots cleared', 'success')
    } catch {
      showToast('Failed to clear slots', 'error')
    }
  }

  const handleClearAll = async () => {
    if (!confirm('Are you sure you want to clear ALL scheduled slots? This cannot be undone.')) return
    try {
      await clearAllSlots.mutateAsync()
      showToast('All slots cleared', 'success')
    } catch {
      showToast('Failed to clear slots', 'error')
    }
  }

  if (isLoading) {
    return <p>Loading schedule...</p>
  }

  return (
    <div class={styles.page}>
      <div class={styles.header}>
        <div class={styles.currentStatus}>
          <strong>Currently Active:</strong>{' '}
          {currentStatus?.has_content ? (
            <>
              {currentStatus.target_type === 'playlist' ? '📋' : '📷'} {currentStatus.target_name}
            </>
          ) : (
            'No content scheduled for this slot'
          )}
        </div>
        <div class={styles.actions}>
          <Button variant="danger" size="small" onClick={handleClearAll}>
            Clear All
          </Button>
        </div>
      </div>

      {/* Selection Toolbar */}
      {selectedSlots.size > 1 && (
        <div class={clsx(styles.selectionToolbar, styles.visible)}>
          <span>{selectedSlots.size} slots selected</span>
          <Button size="small" onClick={() => setBulkModalOpen(true)}>
            Assign Content
          </Button>
          <Button size="small" variant="danger" onClick={handleClearSelected}>
            Clear Selected
          </Button>
          <Button size="small" variant="secondary" onClick={() => setSelectedSlots(new Set())}>
            Cancel
          </Button>
        </div>
      )}

      {/* Timetable */}
      <div class={styles.wrapper}>
        <div class={styles.timetable}>
          {/* Header */}
          <div class={styles.timetableHeader}>
            <div class={clsx(styles.headerCell, styles.timeHeader)}>Time</div>
            {DAY_NAMES.map((day, i) => (
              <div
                key={day}
                class={clsx(styles.headerCell, i === getCurrentDayIndex() && styles.today)}
              >
                {day}
                {i === getCurrentDayIndex() && <div class={styles.dayDate}>Today</div>}
              </div>
            ))}
          </div>

          {/* Body */}
          <div class={styles.timetableBody}>
            {Array.from({ length: 24 }, (_, hour) => (
              <div key={hour} class={styles.timetableRow}>
                <div class={clsx(styles.timeLabel, styles.hourStart)}>{hour.toString().padStart(2, '0')}:00</div>
                {Array.from({ length: 7 }, (_, day) => {
                  const slotKey = `${day}-${hour}`
                  const slot = slots[slotKey]
                  const hasContent = !!slot
                  const isSelected = selectedSlots.has(slotKey)

                  return (
                    <div
                      key={slotKey}
                      class={clsx(styles.dayColumn, styles.hourStart, hasContent && styles.hasContent, isSelected && styles.selected)}
                      onMouseDown={(e) => onSlotMouseDown(e, day, hour)}
                      onMouseEnter={() => onSlotMouseEnter(day, hour)}
                    >
                      {hasContent && (
                        <div
                          class={clsx(styles.slotContent, slot.target_type === 'playlist' && styles.isPlaylist)}
                          style={{ backgroundColor: getColorForId(slot.target_id) }}
                        >
                          <span class={styles.slotName}>{getSlotInfo(slot).name}</span>
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Legend */}
      <ScheduleLegend slots={slots} instances={enabledInstances} playlists={enabledPlaylists} />

      {/* Slot Modal */}
      {slotModalOpen && slotModalData && (
        <SlotModal
          day={slotModalData.day}
          hour={slotModalData.hour}
          existing={slotModalData.existing}
          instances={enabledInstances}
          playlists={enabledPlaylists}
          onSave={handleSaveSlot}
          onClose={() => setSlotModalOpen(false)}
        />
      )}

      {/* Bulk Modal */}
      {bulkModalOpen && (
        <BulkModal
          count={selectedSlots.size}
          instances={enabledInstances}
          playlists={enabledPlaylists}
          onSave={handleBulkAssign}
          onClose={() => setBulkModalOpen(false)}
        />
      )}
    </div>
  )
}

interface ScheduleLegendProps {
  slots: ScheduleSlots
  instances: Array<{ id: string; name: string }>
  playlists: Array<{ id: string; name: string }>
}

const ScheduleLegend = ({ slots, instances, playlists }: ScheduleLegendProps) => {
  const contentMap = new Map<string, { target_type: string; target_id: string }>()
  Object.values(slots).forEach((slot) => {
    contentMap.set(`${slot.target_type}:${slot.target_id}`, slot)
  })

  if (contentMap.size === 0) {
    return (
      <div class={styles.legend}>
        <p class={styles.hint}>Click and drag to select multiple slots</p>
      </div>
    )
  }

  return (
    <div class={styles.legend}>
      <h4>Legend</h4>
      <div class={styles.legendGrid}>
        {[...contentMap.values()].map((slot) => {
          const name =
            slot.target_type === 'playlist'
              ? playlists.find((p) => p.id === slot.target_id)?.name
              : instances.find((i) => i.id === slot.target_id)?.name
          const icon = slot.target_type === 'playlist' ? '📋' : '📷'

          return (
            <div key={`${slot.target_type}:${slot.target_id}`} class={styles.legendItem}>
              <span
                class={styles.legendColor}
                style={{ backgroundColor: getColorForId(slot.target_id) }}
              />
              <span>
                {icon} {name || 'Unknown'}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

interface SlotModalProps {
  day: number
  hour: number
  existing?: { target_type: string; target_id: string }
  instances: Array<{ id: string; name: string }>
  playlists: Array<{ id: string; name: string; items?: Array<unknown> }>
  onSave: (value: string) => void
  onClose: () => void
}

const SlotModal = ({ day, hour, existing, instances, playlists, onSave, onClose }: SlotModalProps) => {
  const [value, setValue] = useState(
    existing ? `${existing.target_type}:${existing.target_id}` : ''
  )

  return (
    <div class={clsx(styles.modalOverlay, styles.active)} onClick={(e) => {
      if ((e.target as HTMLElement).classList.contains(styles.modalOverlay)) onClose()
    }}>
      <div class={styles.modal}>
        <div class={styles.modalHeader}>
          <h3>{DAY_NAMES[day]} {hour.toString().padStart(2, '0')}:00</h3>
          <button class={styles.modalClose} onClick={onClose}>&times;</button>
        </div>
        <div class={styles.modalBody}>
          <div class={styles.formGroup}>
            <label>Content</label>
            <select value={value} onChange={(e) => setValue((e.target as HTMLSelectElement).value)}>
              <option value="">-- Empty (no content) --</option>
              <optgroup label="Plugin Instances">
                {instances.map((inst) => (
                  <option key={inst.id} value={`instance:${inst.id}`}>
                    📷 {inst.name}
                  </option>
                ))}
              </optgroup>
              <optgroup label="Playlists">
                {playlists.map((pl) => (
                  <option key={pl.id} value={`playlist:${pl.id}`}>
                    📋 {pl.name} ({pl.items?.length || 0} items)
                  </option>
                ))}
              </optgroup>
            </select>
          </div>
        </div>
        <div class={styles.modalFooter}>
          <Button variant="secondary" onClick={onClose}>Cancel</Button>
          <Button onClick={() => onSave(value)}>Save</Button>
        </div>
      </div>
    </div>
  )
}

interface BulkModalProps {
  count: number
  instances: Array<{ id: string; name: string }>
  playlists: Array<{ id: string; name: string }>
  onSave: (value: string) => void
  onClose: () => void
}

const BulkModal = ({ count, instances, playlists, onSave, onClose }: BulkModalProps) => {
  const [value, setValue] = useState('')

  return (
    <div class={clsx(styles.modalOverlay, styles.active)} onClick={(e) => {
      if ((e.target as HTMLElement).classList.contains(styles.modalOverlay)) onClose()
    }}>
      <div class={styles.modal}>
        <div class={styles.modalHeader}>
          <h3>Assign to {count} slots</h3>
          <button class={styles.modalClose} onClick={onClose}>&times;</button>
        </div>
        <div class={styles.modalBody}>
          <div class={styles.formGroup}>
            <label>Content</label>
            <select value={value} onChange={(e) => setValue((e.target as HTMLSelectElement).value)}>
              <option value="">-- Select content --</option>
              <optgroup label="Plugin Instances">
                {instances.map((inst) => (
                  <option key={inst.id} value={`instance:${inst.id}`}>
                    📷 {inst.name}
                  </option>
                ))}
              </optgroup>
              <optgroup label="Playlists">
                {playlists.map((pl) => (
                  <option key={pl.id} value={`playlist:${pl.id}`}>
                    📋 {pl.name}
                  </option>
                ))}
              </optgroup>
            </select>
          </div>
        </div>
        <div class={styles.modalFooter}>
          <Button variant="secondary" onClick={onClose}>Cancel</Button>
          <Button onClick={() => onSave(value)}>Assign</Button>
        </div>
      </div>
    </div>
  )
}
