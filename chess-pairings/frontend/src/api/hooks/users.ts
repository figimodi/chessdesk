import { api } from '@/api/client'
import { QueryCacheKeys } from '@/api/queryCacheKeys'
import type { UserCreate, UserUpdate } from '@/api/types'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

export function useUsers() {
  return useQuery({
    queryKey: QueryCacheKeys.users,
    queryFn: api.listUsers,
  })
}

export function useCreateUser() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: UserCreate) => api.createUser(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QueryCacheKeys.users })
    },
  })
}

export function useUpdateUser() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ userId, ...payload }: UserUpdate & { userId: number }) => api.updateUser(userId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QueryCacheKeys.users })
    },
  })
}

export function useDeleteUser() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (userId: number) => api.deleteUser(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QueryCacheKeys.users })
      queryClient.invalidateQueries({ queryKey: QueryCacheKeys.tournaments })
    },
  })
}
