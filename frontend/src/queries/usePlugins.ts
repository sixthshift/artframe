import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { get, post, put, del } from '@/api/client'
import type {
  Plugin,
  PluginInstance,
  CreateInstanceRequest,
  UpdateInstanceRequest,
} from '@/api/types'

// Query keys
export const pluginKeys = {
  all: ['plugins'] as const,
  list: () => [...pluginKeys.all, 'list'] as const,
  detail: (id: string) => [...pluginKeys.all, 'detail', id] as const,
}

export const instanceKeys = {
  all: ['instances'] as const,
  list: () => [...instanceKeys.all, 'list'] as const,
  detail: (id: string) => [...instanceKeys.all, 'detail', id] as const,
}

// Plugins queries
export function usePlugins() {
  return useQuery({
    queryKey: pluginKeys.list(),
    queryFn: () => get<Plugin[]>('/plugins'),
  })
}

export function usePlugin(id: string) {
  return useQuery({
    queryKey: pluginKeys.detail(id),
    queryFn: () => get<Plugin>(`/plugins/${id}`),
    enabled: !!id,
  })
}

// Instances queries
export function useInstances() {
  return useQuery({
    queryKey: instanceKeys.list(),
    queryFn: () => get<PluginInstance[]>('/instances'),
  })
}

export function useInstance(id: string) {
  return useQuery({
    queryKey: instanceKeys.detail(id),
    queryFn: () => get<PluginInstance>(`/instances/${id}`),
    enabled: !!id,
  })
}

// Instance mutations
export function useCreateInstance() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateInstanceRequest) =>
      post<PluginInstance>('/instances', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: instanceKeys.list() })
    },
  })
}

export function useUpdateInstance() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateInstanceRequest }) =>
      put<PluginInstance>(`/instances/${id}`, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: instanceKeys.list() })
      queryClient.invalidateQueries({ queryKey: instanceKeys.detail(id) })
    },
  })
}

export function useDeleteInstance() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => del(`/instances/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: instanceKeys.list() })
    },
  })
}

export function useToggleInstance() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, enable }: { id: string; enable: boolean }) =>
      post(`/instances/${id}/${enable ? 'enable' : 'disable'}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: instanceKeys.list() })
    },
  })
}

export function useTestInstance() {
  return useMutation({
    mutationFn: (id: string) => post(`/instances/${id}/test`),
  })
}
