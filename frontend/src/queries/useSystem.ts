import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { get, post } from '@/api/client'
import type {
  SystemStatus,
  SystemInfo,
  ConnectionStatus,
  SchedulerStatus,
  LogEntry,
  SourceStats,
  DisplayStatus,
  DisplayHealth,
} from '@/api/types'

export const systemKeys = {
  all: ['system'] as const,
  status: () => [...systemKeys.all, 'status'] as const,
  info: () => [...systemKeys.all, 'info'] as const,
  connections: () => [...systemKeys.all, 'connections'] as const,
  scheduler: () => [...systemKeys.all, 'scheduler'] as const,
  logs: (level?: string) => [...systemKeys.all, 'logs', level] as const,
  sourceStats: () => [...systemKeys.all, 'sourceStats'] as const,
}

export const displayKeys = {
  all: ['display'] as const,
  current: () => [...displayKeys.all, 'current'] as const,
  health: () => [...displayKeys.all, 'health'] as const,
}

// System queries
export function useSystemStatus() {
  return useQuery({
    queryKey: systemKeys.status(),
    queryFn: () => get<SystemStatus>('/status'),
    refetchInterval: 10000,
  })
}

export function useSystemInfo() {
  return useQuery({
    queryKey: systemKeys.info(),
    queryFn: () => get<SystemInfo>('/system/info'),
    refetchInterval: 10000,
  })
}

export function useConnections() {
  return useQuery({
    queryKey: systemKeys.connections(),
    queryFn: () => get<ConnectionStatus>('/connections'),
    refetchInterval: 10000,
  })
}

export function useSchedulerStatus() {
  return useQuery({
    queryKey: systemKeys.scheduler(),
    queryFn: () => get<SchedulerStatus>('/scheduler/status'),
    refetchInterval: 10000,
  })
}

export function useLogs(level?: string) {
  return useQuery({
    queryKey: systemKeys.logs(level),
    queryFn: () => get<LogEntry[]>(`/system/logs${level ? `?level=${level}` : ''}`),
  })
}

export function useSourceStats() {
  return useQuery({
    queryKey: systemKeys.sourceStats(),
    queryFn: () => get<SourceStats>('/source/stats'),
    refetchInterval: 30000,
  })
}

// Display queries
export function useCurrentDisplay() {
  return useQuery({
    queryKey: displayKeys.current(),
    queryFn: () => get<DisplayStatus>('/display/current'),
    refetchInterval: 10000,
  })
}

export function useDisplayHealth() {
  return useQuery({
    queryKey: displayKeys.health(),
    queryFn: () => get<DisplayHealth>('/display/health'),
    refetchInterval: 10000,
  })
}

// Mutations
export function useToggleScheduler() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (pause: boolean) =>
      post(`/scheduler/${pause ? 'pause' : 'resume'}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: systemKeys.scheduler() })
    },
  })
}

export function useTriggerUpdate() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => post('/update'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: displayKeys.current() })
      queryClient.invalidateQueries({ queryKey: systemKeys.status() })
    },
  })
}

export function useClearDisplay() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => post('/clear'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: displayKeys.current() })
    },
  })
}
