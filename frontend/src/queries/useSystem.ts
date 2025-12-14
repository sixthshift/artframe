import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { get, post, postFile } from '@/api/client'
import type {
  SystemStatus,
  SystemInfo,
  ConnectionStatus,
  SchedulerStatus,
  LogEntry,
  DisplayStatus,
  DisplayHealth,
  AppConfig,
} from '@/api/types'

export const systemKeys = {
  all: ['system'] as const,
  status: () => [...systemKeys.all, 'status'] as const,
  info: () => [...systemKeys.all, 'info'] as const,
  connections: () => [...systemKeys.all, 'connections'] as const,
  scheduler: () => [...systemKeys.all, 'scheduler'] as const,
  logs: (level?: string) => [...systemKeys.all, 'logs', level] as const,
  config: () => [...systemKeys.all, 'config'] as const,
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
    queryFn: () => get<SystemStatus>('/system/status'),
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
    queryFn: () => get<ConnectionStatus>('/system/connections'),
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

export function useConfig() {
  return useQuery({
    queryKey: systemKeys.config(),
    queryFn: () => get<AppConfig>('/config'),
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

export function useTriggerRefresh() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => post('/display/refresh'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: displayKeys.current() })
      queryClient.invalidateQueries({ queryKey: systemKeys.status() })
    },
  })
}

export function useClearDisplay() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => post('/display/clear'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: displayKeys.current() })
    },
  })
}

export interface HardwareTestResult {
  success: boolean
  message: string
  model?: string
  driver?: string
  display_size?: [number, number]
}

export function useHardwareTest() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => post<HardwareTestResult>('/display/hardware-test'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: displayKeys.current() })
      queryClient.invalidateQueries({ queryKey: displayKeys.health() })
    },
  })
}

export function useUploadImage() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (file: File) => postFile('/display/upload', file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: displayKeys.current() })
    },
  })
}

export function useClearOverride() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => post('/display/clear-override'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: displayKeys.current() })
    },
  })
}
