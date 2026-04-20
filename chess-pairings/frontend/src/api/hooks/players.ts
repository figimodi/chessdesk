import { api } from "@/api/client";
import { QueryCacheKeys } from "@/api/queryCacheKeys";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

export function usePlayers() {
  return useQuery({
    queryKey: QueryCacheKeys.players,
    queryFn: api.listPlayers,
  });
}

export function useFideSearch(query: string, category?: string) {
  return useQuery({
    queryKey: QueryCacheKeys.fideSearch(query, category),
    queryFn: () => api.searchFidePlayers(query, category),
    enabled: query.trim().length >= 2,
  });
}

export function useImportPlayerFromFide() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (fideId: string) => api.importFromFide(fideId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QueryCacheKeys.players });
    },
  });
}
