import type {
  AuthToken,
  FidePlayer,
  PasswordChangeRequest,
  Player,
  Team,
  TournamentCreate,
  TournamentDetail,
  TournamentListItem,
  TournamentPublicRegistration,
  TournamentPlayer,
  TournamentUpdate,
  User,
  UserCreate,
  UserUpdate,
} from '@/api/types'
import { customAxios } from '@/api/customClient'

export const api = {
  async login(payload: { username: string; password: string }) {
    const response = await customAxios.post<AuthToken>('/api/v1/auth/login', payload)
    return response.data
  },
  async getMe() {
    const response = await customAxios.get<User>('/api/v1/auth/me')
    return response.data
  },
  async changePassword(payload: PasswordChangeRequest) {
    const response = await customAxios.post<User>('/api/v1/auth/change-password', payload)
    return response.data
  },
  async listUsers() {
    const response = await customAxios.get<User[]>('/api/v1/admin/users/')
    return response.data
  },
  async createUser(payload: UserCreate) {
    const response = await customAxios.post<User>('/api/v1/admin/users/', payload)
    return response.data
  },
  async updateUser(userId: number, payload: UserUpdate) {
    const response = await customAxios.patch<User>(`/api/v1/admin/users/${userId}`, payload)
    return response.data
  },
  async deleteUser(userId: number) {
    const response = await customAxios.delete<{ ok: boolean }>(`/api/v1/admin/users/${userId}`)
    return response.data
  },
  async listTournaments() {
    const response = await customAxios.get<TournamentListItem[]>('/api/v1/tournaments/')
    return response.data
  },
  async getTournament(id: string) {
    const response = await customAxios.get<TournamentDetail>(`/api/v1/tournaments/${id}`)
    return response.data
  },
  async createTournament(payload: TournamentCreate) {
    const response = await customAxios.post<TournamentListItem>('/api/v1/admin/tournaments/', payload)
    return response.data
  },
  async updateTournament(id: string, payload: TournamentUpdate) {
    const response = await customAxios.put<TournamentListItem>(`/api/v1/admin/tournaments/${id}`, payload)
    return response.data
  },
  async deleteTournament(id: string) {
    const response = await customAxios.delete<{ ok: boolean }>(`/api/v1/admin/tournaments/${id}`)
    return response.data
  },
  async generatePairings(id: string) {
    const response = await customAxios.post(`/api/v1/admin/tournaments/${id}/pairings/generate`)
    return response.data
  },
  async updatePairingResult(tournamentId: string, pairingId: number, result: string) {
    const response = await customAxios.patch(
      `/api/v1/admin/tournaments/${tournamentId}/pairings/results/${pairingId}`,
      { result }
    )
    return response.data
  },
  async deleteLatestRound(tournamentId: string) {
    const response = await customAxios.delete(
      `/api/v1/admin/tournaments/${tournamentId}/pairings/latest-round`
    )
    return response.data
  },
  async closeRegistration(tournamentId: string) {
    const response = await customAxios.post<TournamentListItem>(
      `/api/v1/admin/tournaments/${tournamentId}/close-registration`
    )
    return response.data
  },
  async reopenRegistration(tournamentId: string) {
    const response = await customAxios.post<TournamentListItem>(
      `/api/v1/admin/tournaments/${tournamentId}/reopen-registration`
    )
    return response.data
  },
  async listPlayers() {
    const response = await customAxios.get<Player[]>('/api/v1/players/')
    return response.data
  },
  async searchFidePlayers(query: string, category?: string) {
    const response = await customAxios.get<FidePlayer[]>('/api/v1/players/fide/search', {
      params: { query, category },
    })
    return response.data
  },
  async importFromFide(fideId: string) {
    const response = await customAxios.post<Player>('/api/v1/admin/players/import-from-fide', null, {
      params: { fide_id: fideId },
    })
    return response.data
  },
  async assignPlayer(
    tournamentId: string,
    payload: { player_id: number; team_id?: number | null; allow_late_join?: boolean }
  ) {
    const response = await customAxios.post<TournamentPlayer>(
      `/api/v1/admin/tournaments/${tournamentId}/players`,
      payload
    )
    return response.data
  },
  async removePlayer(tournamentId: string, playerId: number) {
    const response = await customAxios.delete<{ ok: boolean }>(
      `/api/v1/admin/tournaments/${tournamentId}/players/${playerId}`
    )
    return response.data
  },
  async updatePlayerAvailability(
    tournamentId: string,
    playerId: number,
    payload: { round_number: number; is_available: boolean }
  ) {
    const response = await customAxios.patch<TournamentPlayer>(
      `/api/v1/admin/tournaments/${tournamentId}/players/${playerId}/availability`,
      payload
    )
    return response.data
  },
  async updatePlayerStatus(
    tournamentId: string,
    playerId: number,
    payload: { is_active: boolean }
  ) {
    const response = await customAxios.patch<TournamentPlayer>(
      `/api/v1/admin/tournaments/${tournamentId}/players/${playerId}/status`,
      payload
    )
    return response.data
  },
  async listTeams(tournamentId: string) {
    const response = await customAxios.get<Team[]>(`/api/v1/admin/tournaments/${tournamentId}/teams/`)
    return response.data
  },
  async createTeam(tournamentId: string, payload: { name: string }) {
    const response = await customAxios.post<Team>(`/api/v1/admin/tournaments/${tournamentId}/teams/`, payload)
    return response.data
  },
  async updateTeam(tournamentId: string, teamId: number, payload: { name: string }) {
    const response = await customAxios.put<Team>(`/api/v1/admin/tournaments/${tournamentId}/teams/${teamId}`, payload)
    return response.data
  },
  async deleteTeam(tournamentId: string, teamId: number) {
    const response = await customAxios.delete<{ ok: boolean }>(`/api/v1/admin/tournaments/${tournamentId}/teams/${teamId}`)
    return response.data
  },
  async assignTeamMember(tournamentId: string, teamId: number, payload: { player_id: number }) {
    const response = await customAxios.post<Team>(`/api/v1/admin/tournaments/${tournamentId}/teams/${teamId}/members`, payload)
    return response.data
  },
  async removeTeamMember(tournamentId: string, teamId: number, playerId: number) {
    const response = await customAxios.delete<Team>(`/api/v1/admin/tournaments/${tournamentId}/teams/${teamId}/members/${playerId}`)
    return response.data
  },
  async reorderTeamMembers(tournamentId: string, teamId: number, payload: { player_ids: number[] }) {
    const response = await customAxios.patch<Team>(`/api/v1/admin/tournaments/${tournamentId}/teams/${teamId}/members/order`, payload)
    return response.data
  },
  async updateTeamAvailability(tournamentId: string, teamId: number, payload: { round_number: number; is_available: boolean }) {
    const response = await customAxios.patch<Team>(`/api/v1/admin/tournaments/${tournamentId}/teams/${teamId}/availability`, payload)
    return response.data
  },
  async updateTeamStatus(tournamentId: string, teamId: number, payload: { is_active: boolean }) {
    const response = await customAxios.patch<Team>(`/api/v1/admin/tournaments/${tournamentId}/teams/${teamId}/status`, payload)
    return response.data
  },
  async updateTeamLineup(tournamentId: string, teamId: number, payload: { player_id: number; round_number: number; is_selected: boolean }) {
    const response = await customAxios.patch<Team>(`/api/v1/admin/tournaments/${tournamentId}/teams/${teamId}/lineup`, payload)
    return response.data
  },
  async uploadBulletin(tournamentId: string, file: File) {
    const formData = new FormData()
    formData.append('upload', file)
    const response = await customAxios.post(
      `/api/v1/admin/tournaments/${tournamentId}/bulletin`,
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
      }
    )
    return response.data as { bulletinUrl: string }
  },
  async registerToTournament(tournamentId: string, payload: TournamentPublicRegistration) {
    const response = await customAxios.post<TournamentPlayer>(`/api/v1/tournaments/${tournamentId}/register`, payload)
    return response.data
  },
}
