import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { get, post, del } from '@/api/client'
import type {
  ScheduleData,
  CurrentScheduleStatus,
  TimeSlot,
  BulkSlotAssignment,
} from '@/api/types'

export const scheduleKeys = {
  all: ['schedules'] as const,
  slots: () => [...scheduleKeys.all, 'slots'] as const,
  current: () => [...scheduleKeys.all, 'current'] as const,
}

export function useSchedules() {
  return useQuery({
    queryKey: scheduleKeys.slots(),
    queryFn: () => get<ScheduleData>('/schedules'),
  })
}

export function useCurrentSchedule() {
  return useQuery({
    queryKey: scheduleKeys.current(),
    queryFn: () => get<CurrentScheduleStatus>('/schedules/current'),
    refetchInterval: 30000, // Refresh every 30 seconds
  })
}

export function useSetSlot() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (slot: TimeSlot) => post('/schedules/slot', slot),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: scheduleKeys.slots() })
      queryClient.invalidateQueries({ queryKey: scheduleKeys.current() })
    },
  })
}

export function useBulkSetSlots() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: BulkSlotAssignment) => post('/schedules/slots/bulk', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: scheduleKeys.slots() })
      queryClient.invalidateQueries({ queryKey: scheduleKeys.current() })
    },
  })
}

export function useClearSlot() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ day, hour }: { day: number; hour: number }) =>
      del('/schedules/slot', { day, hour }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: scheduleKeys.slots() })
      queryClient.invalidateQueries({ queryKey: scheduleKeys.current() })
    },
  })
}

export function useClearAllSlots() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => post('/schedules/clear'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: scheduleKeys.slots() })
      queryClient.invalidateQueries({ queryKey: scheduleKeys.current() })
    },
  })
}
