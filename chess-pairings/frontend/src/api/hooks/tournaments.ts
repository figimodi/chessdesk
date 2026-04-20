import { api } from "@/api/client";
import { QueryCacheKeys } from "@/api/queryCacheKeys";
import type { TournamentCreate, TournamentUpdate } from "@/api/types";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

export function useTournaments() {
  return useQuery({
    queryKey: QueryCacheKeys.tournaments,
    queryFn: api.listTournaments,
  });
}

export function useTournament(tournamentId: string) {
  return useQuery({
    queryKey: QueryCacheKeys.tournament(tournamentId),
    queryFn: () => api.getTournament(tournamentId),
  });
}

export function useCreateTournament() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: TournamentCreate) => api.createTournament(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QueryCacheKeys.tournaments });
    },
  });
}

export function useUpdateTournament(tournamentId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: TournamentUpdate) => api.updateTournament(tournamentId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QueryCacheKeys.tournaments });
      queryClient.invalidateQueries({ queryKey: QueryCacheKeys.tournament(tournamentId) });
    },
  });
}

export function useDeleteTournament() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (tournamentId: string) => api.deleteTournament(tournamentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QueryCacheKeys.tournaments });
    },
  });
}

export function useGeneratePairings(tournamentId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => api.generatePairings(tournamentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QueryCacheKeys.tournament(tournamentId) });
    },
  });
}

export function useDeleteLatestRound(tournamentId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => api.deleteLatestRound(tournamentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QueryCacheKeys.tournament(tournamentId) });
    },
  });
}

export function useCloseRegistration(tournamentId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => api.closeRegistration(tournamentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QueryCacheKeys.tournament(tournamentId) });
      queryClient.invalidateQueries({ queryKey: QueryCacheKeys.tournaments });
    },
  });
}

export function useReopenRegistration(tournamentId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => api.reopenRegistration(tournamentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QueryCacheKeys.tournament(tournamentId) });
      queryClient.invalidateQueries({ queryKey: QueryCacheKeys.tournaments });
    },
  });
}

export function useAssignPlayer(tournamentId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: { player_id: number; team_id?: number | null; allow_late_join?: boolean }) => api.assignPlayer(tournamentId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QueryCacheKeys.tournament(tournamentId) });
    },
  });
}

export function useUpdatePlayerAvailability(tournamentId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: { playerId: number; round_number: number; is_available: boolean }) =>
      api.updatePlayerAvailability(tournamentId, payload.playerId, {
        round_number: payload.round_number,
        is_available: payload.is_available,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QueryCacheKeys.tournament(tournamentId) });
    },
  });
}

export function useUpdatePlayerStatus(tournamentId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: { playerId: number; is_active: boolean }) =>
      api.updatePlayerStatus(tournamentId, payload.playerId, {
        is_active: payload.is_active,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QueryCacheKeys.tournament(tournamentId) });
    },
  });
}

export function useUploadBulletin(tournamentId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => api.uploadBulletin(tournamentId, file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QueryCacheKeys.tournament(tournamentId) });
      queryClient.invalidateQueries({ queryKey: QueryCacheKeys.tournaments });
    },
  });
}

export function useCreateTeam(tournamentId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: { name: string }) => api.createTeam(tournamentId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QueryCacheKeys.tournament(tournamentId) });
    },
  });
}

export function useUpdateTeam(tournamentId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: { teamId: number; name: string }) => api.updateTeam(tournamentId, payload.teamId, { name: payload.name }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QueryCacheKeys.tournament(tournamentId) });
    },
  });
}

export function useDeleteTeam(tournamentId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (teamId: number) => api.deleteTeam(tournamentId, teamId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QueryCacheKeys.tournament(tournamentId) });
    },
  });
}

export function useAssignTeamMember(tournamentId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: { teamId: number; player_id: number }) => api.assignTeamMember(tournamentId, payload.teamId, { player_id: payload.player_id }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QueryCacheKeys.tournament(tournamentId) });
    },
  });
}

export function useRemoveTeamMember(tournamentId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: { teamId: number; playerId: number }) => api.removeTeamMember(tournamentId, payload.teamId, payload.playerId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QueryCacheKeys.tournament(tournamentId) });
    },
  });
}

export function useReorderTeamMembers(tournamentId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: { teamId: number; player_ids: number[] }) => api.reorderTeamMembers(tournamentId, payload.teamId, { player_ids: payload.player_ids }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QueryCacheKeys.tournament(tournamentId) });
    },
  });
}

export function useUpdateTeamAvailability(tournamentId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: { teamId: number; round_number: number; is_available: boolean }) =>
      api.updateTeamAvailability(tournamentId, payload.teamId, {
        round_number: payload.round_number,
        is_available: payload.is_available,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QueryCacheKeys.tournament(tournamentId) });
    },
  });
}

export function useUpdateTeamStatus(tournamentId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: { teamId: number; is_active: boolean }) =>
      api.updateTeamStatus(tournamentId, payload.teamId, { is_active: payload.is_active }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QueryCacheKeys.tournament(tournamentId) });
    },
  });
}

export function useUpdateTeamLineup(tournamentId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: { teamId: number; player_id: number; round_number: number; is_selected: boolean }) =>
      api.updateTeamLineup(tournamentId, payload.teamId, {
        player_id: payload.player_id,
        round_number: payload.round_number,
        is_selected: payload.is_selected,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QueryCacheKeys.tournament(tournamentId) });
    },
  });
}
