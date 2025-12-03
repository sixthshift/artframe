import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { get, post, put, del } from '@/api/client'
import type { Playlist, CreatePlaylistRequest } from '@/api/types'

export const playlistKeys = {
  all: ['playlists'] as const,
  list: () => [...playlistKeys.all, 'list'] as const,
  detail: (id: string) => [...playlistKeys.all, 'detail', id] as const,
}

export function usePlaylists() {
  return useQuery({
    queryKey: playlistKeys.list(),
    queryFn: () => get<Playlist[]>('/playlists'),
  })
}

export function usePlaylist(id: string) {
  return useQuery({
    queryKey: playlistKeys.detail(id),
    queryFn: () => get<Playlist>(`/playlists/${id}`),
    enabled: !!id,
  })
}

export function useCreatePlaylist() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreatePlaylistRequest) =>
      post<Playlist>('/playlists', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: playlistKeys.list() })
    },
  })
}

export function useUpdatePlaylist() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Playlist> }) =>
      put<Playlist>(`/playlists/${id}`, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: playlistKeys.list() })
      queryClient.invalidateQueries({ queryKey: playlistKeys.detail(id) })
    },
  })
}

export function useDeletePlaylist() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => del(`/playlists/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: playlistKeys.list() })
    },
  })
}
