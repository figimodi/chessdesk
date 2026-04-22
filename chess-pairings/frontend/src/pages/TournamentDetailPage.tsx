import { Fragment, useEffect, useMemo, useState, type ReactNode } from "react";
import { isAxiosError } from "axios";
import { Link, Navigate, useNavigate, useParams } from "react-router-dom";
import { CalendarDays, ChartColumn, Clock3, Hash, MapPin, Paperclip, SquarePen, Trash2, User, Users, Zap, Turtle } from "lucide-react";
import { api } from "@/api/client";
import { useFideSearch, useImportPlayerFromFide } from "@/api/hooks/players";
import {
  useAssignTeamMember,
  useAssignPlayer,
  useCloseRegistration,
  useCreateTeam,
  useRemovePlayer,
  useDeleteTeam,
  useDeleteLatestRound,
  useGeneratePairings,
  useUpdatePairingBoardOrder,
  useReorderTeamMembers,
  useReopenRegistration,
  useRemoveTeamMember,
  useTournament,
  useUpdateTeamAvailability,
  useUpdateTeamLineup,
  useUpdateTeamStatus,
  useUpdatePlayerAvailability,
  useUpdatePlayerStatus,
  useUploadBulletin,
} from "@/api/hooks/tournaments";
import type { FidePlayer, PairingResult, TournamentPlayer } from "@/api/types";
import { AppShell } from "@/components/layout/AppShell";
import { RoundsPanel } from "@/components/pairings/RoundsPanel";
import { TeamsPanel } from "@/components/teams/TeamsPanel";
import { AlertCard } from "@/components/ui/alert-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { queryClient } from "@/api/queryClient";
import { getFederationFlagUrl } from "@/lib/federationFlags";
import { useAuth } from "@/auth/AuthContext";
import { TournamentHeroCard } from "@/components/tournaments/TournamentHeroCard";
import { TournamentRegistrationDialog } from "@/components/tournaments/TournamentRegistrationDialog";

export function TournamentDetailPage() {
  const { isAuthenticated, user } = useAuth();
  const { tournamentId = "" } = useParams();
  const navigate = useNavigate();
  const { data: tournament, isError } = useTournament(tournamentId);
  const assignMutation = useAssignPlayer(tournamentId);
  const removePlayerMutation = useRemovePlayer(tournamentId);
  const createTeamMutation = useCreateTeam(tournamentId);
  const deleteTeamMutation = useDeleteTeam(tournamentId);
  const assignTeamMemberMutation = useAssignTeamMember(tournamentId);
  const removeTeamMemberMutation = useRemoveTeamMember(tournamentId);
  const reorderTeamMembersMutation = useReorderTeamMembers(tournamentId);
  const updateTeamAvailabilityMutation = useUpdateTeamAvailability(tournamentId);
  const updateTeamStatusMutation = useUpdateTeamStatus(tournamentId);
  const updateTeamLineupMutation = useUpdateTeamLineup(tournamentId);
  const closeRegistrationMutation = useCloseRegistration(tournamentId);
  const reopenRegistrationMutation = useReopenRegistration(tournamentId);
  const updateAvailabilityMutation = useUpdatePlayerAvailability(tournamentId);
  const updatePlayerStatusMutation = useUpdatePlayerStatus(tournamentId);
  const importMutation = useImportPlayerFromFide();
  const generateMutation = useGeneratePairings(tournamentId);
  const deleteRoundMutation = useDeleteLatestRound(tournamentId);
  const updatePairingBoardOrderMutation = useUpdatePairingBoardOrder(tournamentId);
  const uploadMutation = useUploadBulletin(tournamentId);
  const [catalogQuery, setCatalogQuery] = useState("");
  const [debouncedCatalogQuery, setDebouncedCatalogQuery] = useState("");
  const [catalogPage, setCatalogPage] = useState(1);
  const [activeTab, setActiveTab] = useState<"participants" | "teams" | "standings" | "rounds">("participants");
  const [isTournamentConcluded, setIsTournamentConcluded] = useState(false);
  const [expandedTeamStandingId, setExpandedTeamStandingId] = useState<number | null>(null);
  const [alertMessage, setAlertMessage] = useState("");
  const [isRegistrationDialogOpen, setIsRegistrationDialogOpen] = useState(false);
  const [selectedPlayerForManagement, setSelectedPlayerForManagement] = useState<number | null>(null);
  const [selectedParticipantId, setSelectedParticipantId] = useState<number | null>(null);
  const [confirmDialog, setConfirmDialog] = useState<{
    title: string;
    description: string;
    confirmLabel?: string;
    confirmVariant?: "default" | "destructive";
    action: () => Promise<void> | void;
  } | null>(null);

  useEffect(() => {
    const timeout = window.setTimeout(() => {
      setDebouncedCatalogQuery(catalogQuery);
    }, 1000);

    return () => window.clearTimeout(timeout);
  }, [catalogQuery]);

  useEffect(() => {
    setCatalogPage(1);
  }, [debouncedCatalogQuery]);

  const { data: catalogPlayers, isFetching: isSearchingCatalog } = useFideSearch(debouncedCatalogQuery, tournament?.time_control_category);

  const unassignedCatalogPlayers = (catalogPlayers ?? []).filter(
    (player) => !(tournament?.players.some((entry) => entry.fide_id === player.fide_id) ?? false),
  );

  const handleResultChange = async (pairingId: number, result: PairingResult, currentResult: PairingResult) => {
    const runUpdate = async () => {
      await api.updatePairingResult(tournamentId, pairingId, result);
      queryClient.invalidateQueries({ queryKey: ["tournaments", tournamentId] });
    };

    if (currentResult !== "unplayed" && currentResult !== result) {
      setConfirmDialog({
        title: "Conferma modifica risultato",
        description: "Sei sicuro di voler cambiare il risultato di questo match?",
        confirmLabel: "Conferma modifica",
        action: runUpdate,
      });
      return;
    }

    try {
      await runUpdate();
    } catch (error) {
      setAlertMessage(readErrorMessage(error));
    }
  };

  const handleAddParticipant = async (fideId: string) => {
    try {
      const importedPlayer = await importMutation.mutateAsync(fideId);
      await assignMutation.mutateAsync({ player_id: importedPlayer.id });
      setCatalogQuery("");
      setDebouncedCatalogQuery("");
    } catch (error) {
      const message = readErrorMessage(error);
      if (message.includes("solo dal turno")) {
        const nextRound = message.match(/turno (\d+)/)?.[1] ?? "1";
        setConfirmDialog({
          title: "Aggiunta giocatore a iscrizioni chiuse",
          description: `Le iscrizioni sono chiuse. Si vuole aggiungere comunque il giocatore dal turno ${nextRound}?`,
          confirmLabel: `Aggiungi dal turno ${nextRound}`,
          action: async () => {
            const importedPlayer = await importMutation.mutateAsync(fideId);
            await assignMutation.mutateAsync({ player_id: importedPlayer.id, allow_late_join: true });
            setCatalogQuery("");
            setDebouncedCatalogQuery("");
          },
        });
      } else {
        setAlertMessage(message);
      }
    }
  };

  const generatedRounds = tournament?.rounds.filter((round) => round.pairings.length > 0) ?? [];
  const nextRoundNumber = generatedRounds.length + 1;
  const isTeamLikeTournament = tournament?.type === "team" || tournament?.type === "quadriglia";
  const participantLabel = isTeamLikeTournament ? "Squadre" : "Giocatori";

  const catalogRatingLabel =
    tournament?.time_control_category === "blitz" ? "ELO Blitz" : tournament?.time_control_category === "rapid" ? "ELO Rapid" : "ELO Standard";

  const getCatalogRating = (player: FidePlayer) => {
    if (tournament?.time_control_category === "blitz") {
      return player.blitz_rating ?? player.rating ?? "-";
    }
    if (tournament?.time_control_category === "rapid") {
      return player.rapid_rating ?? player.rating ?? "-";
    }
    return player.standard_rating ?? player.rating ?? "-";
  };

  const getTournamentPlayerRating = (player: (typeof sortedParticipants)[number]) => {
    if (tournament?.time_control_category === "blitz") {
      return player.blitz_rating ?? player.rating ?? "-";
    }
    if (tournament?.time_control_category === "rapid") {
      return player.rapid_rating ?? player.rating ?? "-";
    }
    return player.rating ?? "-";
  };

  const sortedParticipants = [...(tournament?.players ?? [])].sort((left, right) => {
    const leftRating = Number(getTournamentPlayerRating(left) || 0);
    const rightRating = Number(getTournamentPlayerRating(right) || 0);
    return rightRating - leftRating || left.full_name.localeCompare(right.full_name);
  });

  const sortedStandings = useMemo(() => [...(tournament?.standings ?? [])], [tournament?.standings]);
  const latestGeneratedRound = generatedRounds[generatedRounds.length - 1];
  const allResultsEnteredForLatestRound = latestGeneratedRound
    ? latestGeneratedRound.pairings.every((pairing) => pairing.result !== "unplayed")
    : true;
  const canGenerateNextRound = generatedRounds.length < (tournament?.rounds_count ?? 0) && allResultsEnteredForLatestRound;
  const showConcludeTournament =
    !!tournament?.is_registration_closed && generatedRounds.length === (tournament?.rounds_count ?? 0) && generatedRounds.length > 0;
  const canConcludeTournament = showConcludeTournament && allResultsEnteredForLatestRound;
  const tieBreakLabels: Record<string, string> = {
    buchholz_cut1: "BH/C1",
    buchholz: "BH",
    sonneborn_berger: "SB",
    rating: "Elo",
    direct_encounter: "Scontro diretto",
    wins_black: "Vittorie/Nero",
    played_games: "Partite",
    individual_points: "Punti ind.",
    head_to_head: tournament?.type === "quadriglia" ? "Class. avulsa" : "Class. avulsa (PS/PI)",
    weighted_sonneborn: "Sonneborn pes.",
  };
  const visibleStandingsTieBreaks =
    tournament?.tie_breaks.filter((criterion) => criterion !== "direct_encounter" && criterion !== "wins_black") ?? [];
  const visibleTeamTieBreaks = tournament?.type === "quadriglia"
    ? tournament?.tie_breaks.filter((criterion) => criterion !== "individual_points" && criterion !== "weighted_sonneborn") ?? []
    : tournament?.tie_breaks ?? [];

  useEffect(() => {
    if (!canConcludeTournament) {
      setIsTournamentConcluded(false);
    }
  }, [canConcludeTournament]);

  if (isError) {
    return <AppShell>Torneo non trovato o non accessibile.</AppShell>;
  }

  if (!tournament) {
    return <AppShell>Caricamento torneo...</AppShell>;
  }

  if (isAuthenticated && user?.must_change_password) {
    return <Navigate replace to="/change-password" />;
  }

  const canManage = isAuthenticated && tournament.can_manage;

  const catalogPageSize = 5;
  const catalogTotalPages = Math.max(1, Math.ceil(unassignedCatalogPlayers.length / catalogPageSize));
  const safeCatalogPage = Math.min(catalogPage, catalogTotalPages);
  const paginatedCatalogPlayers = unassignedCatalogPlayers.slice((safeCatalogPage - 1) * catalogPageSize, safeCatalogPage * catalogPageSize);

  const managedPlayer = sortedParticipants.find((player) => player.player_id === selectedPlayerForManagement) ?? null;

  const handleGenerateRound = async () => {
    try {
      if (!tournament.is_registration_closed && nextRoundNumber === 1) {
        setConfirmDialog({
          title: "Chiudere iscrizioni e generare turno 1",
          description: "Le iscrizioni non sono ancora chiuse. Vuoi chiudere le iscrizioni e generare subito il turno 1?",
          confirmLabel: "Chiudi e genera",
          action: async () => {
            await closeRegistrationMutation.mutateAsync();
            await generateMutation.mutateAsync();
            setActiveTab("rounds");
          },
        });
        return;
      }
      await generateMutation.mutateAsync();
      setActiveTab("rounds");
    } catch (error) {
      setAlertMessage(readErrorMessage(error));
    }
  };

  const handleConcludeTournament = () => {
    setIsTournamentConcluded(true);
    setActiveTab("standings");
  };

  return (
    <AppShell>
      {isRegistrationDialogOpen ? <TournamentRegistrationDialog onClose={() => setIsRegistrationDialogOpen(false)} tournament={tournament} /> : null}
      {alertMessage ? <AlertCard message={alertMessage} onClose={() => setAlertMessage("")} /> : null}
      <ConfirmDialog
        open={confirmDialog !== null}
        title={confirmDialog?.title ?? ""}
        description={confirmDialog?.description ?? ""}
        confirmLabel={confirmDialog?.confirmLabel}
        confirmVariant={confirmDialog?.confirmVariant}
        onCancel={() => setConfirmDialog(null)}
        onConfirm={async () => {
          if (!confirmDialog) return;
          try {
            await confirmDialog.action();
          } catch (error) {
            setAlertMessage(readErrorMessage(error));
          } finally {
            setConfirmDialog(null);
          }
        }}
      />
      {managedPlayer && canManage && !isTeamLikeTournament ? (
        <PlayerAvailabilityDialog
          player={managedPlayer}
          roundsCount={tournament.rounds_count}
          onClose={() => setSelectedPlayerForManagement(null)}
          onToggleAvailability={(roundNumber, isAvailable) =>
            updateAvailabilityMutation.mutate({
              playerId: managedPlayer.player_id,
              round_number: roundNumber,
              is_available: !isAvailable,
            })
          }
          onToggleStatus={() =>
            updatePlayerStatusMutation.mutate({
              playerId: managedPlayer.player_id,
              is_active: !managedPlayer.is_active,
            })
          }
        />
      ) : null}
      <section className="mb-8">
        <TournamentHeroCard
          bulletinUrl={tournament.bulletin_url}
          datesLabel={formatTournamentDates(tournament.start_date, tournament.end_date, tournament.rounds)}
          description={tournament.description}
          isEloRated={tournament.is_elo_rated}
          isOwner={user?.id === tournament.owner_id}
          isPrivate={tournament.is_private}
          name={tournament.name}
          onRegister={!tournament.is_private && !tournament.is_registration_closed ? () => setIsRegistrationDialogOpen(true) : undefined}
          participantsLabel={`${isTeamLikeTournament ? tournament.teams_count : tournament.players_count}`}
          registerButtonLabel="Iscriviti"
          roundsLabel={`${tournament.rounds_count} turni`}
          secondaryActions={
            canManage ? (
              <>
                <Button
                  variant="outline"
                  asChild
                  className="border-blue-200 bg-blue-50 text-blue-700 hover:bg-blue-100"
                  aria-label="Modifica torneo"
                  title="Modifica torneo"
                >
                  <Link to={`/tournaments/${tournament.id}/edit`}>
                    <SquarePen className="h-4 w-4" />
                  </Link>
                </Button>
                <Button
                  variant="outline"
                  className="border-red-200 bg-red-50 text-red-600 hover:bg-red-100"
                  aria-label="Elimina torneo"
                  title="Elimina torneo"
                  onClick={() => {
                    setConfirmDialog({
                      title: "Elimina torneo",
                      description: "Sei sicuro di voler eliminare questo torneo?",
                      confirmLabel: "Elimina torneo",
                      confirmVariant: "destructive",
                      action: async () => {
                        await api.deleteTournament(String(tournament.id));
                        navigate("/");
                      },
                    });
                  }}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </>
            ) : null
          }
          timeControl={tournament.time_control}
          timeControlCategory={tournament.time_control_category}
          type={tournament.type}
          venueLabel={tournament.venue ?? "Sede da definire"}
        />
      </section>

      <section className="space-y-4">
        <div className="flex flex-wrap gap-2">
          <Button variant={activeTab === "participants" ? "default" : "outline"} size="sm" onClick={() => setActiveTab("participants")}>
            Partecipanti
          </Button>
          {isTeamLikeTournament ? (
            <Button variant={activeTab === "teams" ? "default" : "outline"} size="sm" onClick={() => setActiveTab("teams")}>
              Squadre
            </Button>
          ) : null}
          <Button variant={activeTab === "standings" ? "default" : "outline"} size="sm" onClick={() => setActiveTab("standings")}>
            Classifica
          </Button>
          <Button variant={activeTab === "rounds" ? "default" : "outline"} size="sm" onClick={() => setActiveTab("rounds")}>
            Turni
          </Button>
        </div>

        {activeTab === "participants" ? (
          <Card>
            <CardHeader>
              <CardTitle>Partecipanti</CardTitle>
              <CardDescription>Cerca un giocatore nel catalogo e aggiungilo direttamente al torneo.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {canManage ? (
                <Card className="border border-dashed">
                  <CardHeader>
                    <CardTitle className="text-lg">Ricerca giocatori</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <Input
                      placeholder="Cerca giocatore per nome o ID FIDE"
                      value={catalogQuery}
                      onChange={(event) => setCatalogQuery(event.target.value)}
                    />

                    {debouncedCatalogQuery.trim().length >= 2 ? (
                      <div className="overflow-x-auto">
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead className="w-12" />
                              <TableHead>Nome</TableHead>
                              <TableHead>FIDE ID</TableHead>
                              <TableHead>FED</TableHead>
                              <TableHead>{catalogRatingLabel}</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {paginatedCatalogPlayers.map((player) => (
                              <TableRow key={player.fide_id}>
                                <TableCell className="text-center">
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => handleAddParticipant(player.fide_id)}
                                    aria-label="Importa giocatore"
                                  >
                                    +
                                  </Button>
                                </TableCell>
                                <TableCell className="min-w-56">{player.full_name}</TableCell>
                                <TableCell>{player.fide_id}</TableCell>
                                <TableCell>
                                  <FederationCell federation={player.federation} />
                                </TableCell>
                                <TableCell>{getCatalogRating(player)}</TableCell>
                              </TableRow>
                            ))}
                            {!unassignedCatalogPlayers.length ? (
                              <TableRow>
                                <TableCell colSpan={5}>
                                  {isSearchingCatalog ? "Ricerca in corso..." : "Nessun giocatore disponibile da aggiungere."}
                                </TableCell>
                              </TableRow>
                            ) : null}
                          </TableBody>
                        </Table>
                      </div>
                    ) : null}
                    {debouncedCatalogQuery.trim().length >= 2 && unassignedCatalogPlayers.length > catalogPageSize ? (
                      <div className="flex items-center justify-between gap-3">
                        <div className="text-sm text-[var(--muted-foreground)]">
                          Pagina {safeCatalogPage} di {catalogTotalPages}
                        </div>
                        <div className="flex gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            disabled={safeCatalogPage <= 1}
                            onClick={() => setCatalogPage((current) => Math.max(1, current - 1))}
                          >
                            Prec.
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            disabled={safeCatalogPage >= catalogTotalPages}
                            onClick={() => setCatalogPage((current) => Math.min(catalogTotalPages, current + 1))}
                          >
                            Succ.
                          </Button>
                        </div>
                      </div>
                    ) : null}
                  </CardContent>
                </Card>
              ) : null}

              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>N. partenza</TableHead>
                      <TableHead>Nome</TableHead>
                      <TableHead>FIDE ID</TableHead>
                      <TableHead>FED</TableHead>
                      <TableHead>{catalogRatingLabel}</TableHead>
                      <TableHead>Anno nascita</TableHead>
                      {isTeamLikeTournament ? <TableHead>Team</TableHead> : null}
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {sortedParticipants.map((player, index) => (
                      <TableRow
                        key={player.player_id}
                        className={[
                          !canManage ? "cursor-default" : "cursor-pointer",
                          selectedParticipantId === player.player_id ? "bg-[var(--muted)]" : "",
                        ].join(" ")}
                        onClick={() => {
                          if (!canManage) return;
                          setSelectedParticipantId((current) => (current === player.player_id ? null : player.player_id));
                        }}
                      >
                        <TableCell>{player.seed_number ?? index + 1}</TableCell>
                        <TableCell className="min-w-56">{player.full_name}</TableCell>
                        <TableCell>{player.fide_id ?? "-"}</TableCell>
                        <TableCell>
                          <FederationCell federation={player.federation} />
                        </TableCell>
                        <TableCell>{getTournamentPlayerRating(player)}</TableCell>
                        <TableCell>{player.birth_year ?? "-"}</TableCell>
                        {isTeamLikeTournament ? <TableCell>{player.team_name ?? "-"}</TableCell> : null}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>

              {canManage && selectedParticipantId ? (
                <div className="flex justify-end gap-3">
                  {!isTeamLikeTournament ? (
                    <Button variant="outline" onClick={() => setSelectedPlayerForManagement(selectedParticipantId)}>
                      Gestisci partecipante
                    </Button>
                  ) : null}
                  <Button
                    variant="outline"
                    className="border-red-200 bg-red-50 text-red-600 hover:bg-red-100"
                    aria-label="Elimina partecipante"
                    title="Elimina partecipante"
                    onClick={() => {
                      const selectedParticipant = sortedParticipants.find((player) => player.player_id === selectedParticipantId);
                      if (!selectedParticipant) return;
                      setConfirmDialog({
                        title: "Rimuovi partecipante",
                        description: `Vuoi davvero rimuovere ${selectedParticipant.full_name} dal torneo?`,
                        confirmLabel: "Rimuovi partecipante",
                        confirmVariant: "destructive",
                        action: async () => {
                          await removePlayerMutation.mutateAsync(selectedParticipant.player_id);
                          setSelectedParticipantId(null);
                          if (selectedPlayerForManagement === selectedParticipant.player_id) {
                            setSelectedPlayerForManagement(null);
                          }
                        },
                      });
                    }}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              ) : null}

              {canManage ? (
                <div className="flex justify-end">
                  <Button
                    variant={tournament.is_registration_closed ? "destructive" : "default"}
                    onClick={() => {
                      if (tournament.is_registration_closed) {
                        setConfirmDialog({
                          title: "Riapri iscrizioni",
                          description: "Sei sicuro di voler riaprire le iscrizioni del torneo?",
                          confirmLabel: "Riapri iscrizioni",
                          confirmVariant: "destructive",
                          action: async () => {
                            await reopenRegistrationMutation.mutateAsync();
                          },
                        });
                        return;
                      }
                      setConfirmDialog({
                        title: "Chiudi iscrizioni",
                        description:
                          "Sei sicuro di voler chiudere le iscrizioni del torneo? Dopo la chiusura non potrai aggiungere altri partecipanti.",
                        confirmLabel: "Chiudi iscrizioni",
                        action: async () => {
                          await closeRegistrationMutation.mutateAsync();
                        },
                      });
                    }}
                    disabled={closeRegistrationMutation.isPending || reopenRegistrationMutation.isPending}
                  >
                    {tournament.is_registration_closed ? "Riapri iscrizioni" : "Chiudi iscrizioni"}
                  </Button>
                </div>
              ) : null}
            </CardContent>
          </Card>
        ) : null}

        {activeTab === "teams" && isTeamLikeTournament ? (
          <TeamsPanel
            canManage={canManage}
            teams={tournament.teams}
            players={tournament.players}
            roundsCount={tournament.rounds_count}
            boardsPerMatch={tournament.boards_per_match ?? 0}
            category={tournament.time_control_category}
            registrationClosed={tournament.is_registration_closed}
            allowOrderEditWhenClosed={!tournament.enforce_board_order}
            onCreateTeam={(name) => createTeamMutation.mutate({ name })}
            onDeleteTeam={(teamId) => deleteTeamMutation.mutate(teamId)}
            onAssignMember={(teamId, playerId) => assignTeamMemberMutation.mutate({ teamId, player_id: playerId })}
            onRemoveMember={(teamId, playerId) => removeTeamMemberMutation.mutate({ teamId, playerId })}
            onReorderMembers={(teamId, player_ids) => reorderTeamMembersMutation.mutate({ teamId, player_ids })}
            onToggleTeamAvailability={(teamId, roundNumber, isAvailable) =>
              updateTeamAvailabilityMutation.mutate({
                teamId,
                round_number: roundNumber,
                is_available: isAvailable,
              })
            }
            onToggleTeamStatus={(teamId, isActive) =>
              updateTeamStatusMutation.mutate({
                teamId,
                is_active: isActive,
              })
            }
            onToggleTeamLineup={(teamId, playerId, roundNumber, isSelected) =>
              updateTeamLineupMutation.mutate({
                teamId,
                player_id: playerId,
                round_number: roundNumber,
                is_selected: isSelected,
              })
            }
          />
        ) : null}

        {activeTab === "standings" ? (
          <Card>
            <CardHeader>
              <CardTitle>Classifica</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {isTeamLikeTournament ? (
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>#</TableHead>
                        <TableHead>Squadra</TableHead>
                        <TableHead>Punti squadra</TableHead>
                        {visibleTeamTieBreaks.map((criterion) => (
                          <TableHead key={criterion}>{tieBreakLabels[criterion] ?? criterion}</TableHead>
                        ))}
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {tournament.team_standings.map((entry, index) => (
                        <Fragment key={entry.team_id}>
                          <TableRow
                            key={entry.team_id}
                            className="cursor-pointer"
                            onClick={() => setExpandedTeamStandingId((current) => (current === entry.team_id ? null : entry.team_id))}
                          >
                            <TableCell>{index + 1}</TableCell>
                            <TableCell>{entry.name}</TableCell>
                            <TableCell>{formatScore(entry.match_points)}</TableCell>
                            {visibleTeamTieBreaks.map((criterion) => (
                              <TableCell key={criterion}>{renderTeamTieBreakValue(entry, criterion, tournament.type)}</TableCell>
                            ))}
                          </TableRow>
                          {expandedTeamStandingId === entry.team_id ? (
                            <TableRow key={`${entry.team_id}-members`}>
                              <TableCell colSpan={3 + visibleTeamTieBreaks.length} className="bg-[var(--muted)]/30">
                                <div className="overflow-x-auto">
                                  <Table>
                                    <TableHeader>
                                      <TableRow>
                                        <TableHead>N°</TableHead>
                                        <TableHead>Giocatore</TableHead>
                                        <TableHead>FED</TableHead>
                                        <TableHead>Punti</TableHead>
                                        <TableHead>{catalogRatingLabel}</TableHead>
                                        <TableHead>ARO</TableHead>
                                        <TableHead>PR</TableHead>
                                        {tournament.is_elo_rated ? <TableHead>Var. Elo</TableHead> : null}
                                      </TableRow>
                                    </TableHeader>
                                    <TableBody>
                                      {sortedStandings
                                        .filter((standing) => standing.team_id === entry.team_id)
                                        .sort(
                                          (left, right) =>
                                            (left.team_board_order ?? 10 ** 9) - (right.team_board_order ?? 10 ** 9) ||
                                            left.full_name.localeCompare(right.full_name),
                                        )
                                        .map((standing) => (
                                          <TableRow key={standing.player_id}>
                                            <TableCell>{standing.seed_number ?? "-"}</TableCell>
                                            <TableCell>{standing.full_name}</TableCell>
                                            <TableCell>
                                              <FederationCell federation={standing.federation} />
                                            </TableCell>
                                            <TableCell>{formatScore(standing.points)}</TableCell>
                                            <TableCell>{getStandingRating(standing, tournament.time_control_category)}</TableCell>
                                            <TableCell>{standing.average_opponent_rating ?? "-"}</TableCell>
                                            <TableCell>{standing.performance_rating ?? "-"}</TableCell>
                                            {tournament.is_elo_rated ? <TableCell>{formatEloChange(standing.elo_change)}</TableCell> : null}
                                          </TableRow>
                                        ))}
                                    </TableBody>
                                  </Table>
                                </div>
                              </TableCell>
                            </TableRow>
                          ) : null}
                        </Fragment>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>#</TableHead>
                        <TableHead>N°</TableHead>
                        <TableHead>Giocatore</TableHead>
                        <TableHead>FED</TableHead>
                        <TableHead>Punti</TableHead>
                        <TableHead>{catalogRatingLabel}</TableHead>
                        {visibleStandingsTieBreaks.map((criterion) => (
                          <TableHead key={criterion}>{tieBreakLabels[criterion] ?? criterion}</TableHead>
                        ))}
                        <TableHead>ARO</TableHead>
                        <TableHead>PR</TableHead>
                        {tournament.is_elo_rated ? <TableHead>Var. Elo</TableHead> : null}
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {sortedStandings.map((entry, index) => (
                        <TableRow key={entry.player_id}>
                          <TableCell>{index + 1}</TableCell>
                          <TableCell>{entry.seed_number ?? "-"}</TableCell>
                          <TableCell>{entry.full_name}</TableCell>
                          <TableCell>
                            <FederationCell federation={entry.federation} />
                          </TableCell>
                          <TableCell>{formatScore(entry.points)}</TableCell>
                          <TableCell>{getStandingRating(entry, tournament.time_control_category)}</TableCell>
                          {visibleStandingsTieBreaks.map((criterion) => (
                            <TableCell key={criterion}>{renderTieBreakValue(entry, criterion, tournament.time_control_category)}</TableCell>
                          ))}
                          <TableCell>{entry.average_opponent_rating ?? "-"}</TableCell>
                          <TableCell>{entry.performance_rating ?? "-"}</TableCell>
                          {tournament.is_elo_rated ? <TableCell>{formatEloChange(entry.elo_change)}</TableCell> : null}
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}
            </CardContent>
          </Card>
        ) : null}

        {activeTab === "rounds" ? (
          <RoundsPanel
            canManage={canManage}
            rounds={generatedRounds}
            standings={tournament.standings}
            players={tournament.players}
            tournamentType={tournament.type}
            category={tournament.time_control_category}
            totalRounds={tournament.rounds_count}
            nextRoundNumber={nextRoundNumber}
            registrationClosed={tournament.is_registration_closed}
            canGenerateNextRound={!!canGenerateNextRound}
            onGenerateRound={handleGenerateRound}
            showConcludeTournament={showConcludeTournament}
            canConcludeTournament={canConcludeTournament}
            isTournamentConcluded={isTournamentConcluded}
            onConcludeTournament={handleConcludeTournament}
            onDeleteLatestRound={() => {
              const latestRound = generatedRounds[generatedRounds.length - 1];
              if (!latestRound) return;
              setConfirmDialog({
                title: `Elimina turno ${latestRound.number}`,
                description: "Sei sicuro di voler eliminare l'ultimo turno generato?",
                confirmLabel: "Elimina turno",
                confirmVariant: "destructive",
                action: async () => {
                  await deleteRoundMutation.mutateAsync();
                },
              });
            }}
            isGenerating={generateMutation.isPending}
            isDeleting={deleteRoundMutation.isPending}
            onResultChange={handleResultChange}
            onPairingBoardMove={(pairingId, side, target_pairing_id) => updatePairingBoardOrderMutation.mutate({ pairingId, side, target_pairing_id })}
            canReorderTeamBoards={isTeamLikeTournament && !tournament.enforce_board_order}
          />
        ) : null}
      </section>
    </AppShell>
  );
}

function InfoChip({ icon, label, href }: { icon: ReactNode; label: string; href?: string }) {
  const content = (
    <>
      <span className="text-[var(--muted-foreground)]">{icon}</span>
      <span className="text-[var(--muted-foreground)]">{label}</span>
    </>
  );

  if (href) {
    return (
      <a
        className="inline-flex items-center gap-2 rounded-full border bg-white px-2.5 py-1 text-xs hover:bg-[var(--muted)]"
        href={href}
        target="_blank"
        rel="noreferrer"
      >
        {content}
      </a>
    );
  }

  return <div className="inline-flex items-center gap-2 rounded-full border bg-white px-2.5 py-1 text-xs">{content}</div>;
}

function InlineDetail({ icon, label, value }: { icon: ReactNode; label: string; value: string }) {
  return (
    <div className="flex min-w-0 items-start gap-3">
      <div className="rounded-2xl border bg-white p-2.5 text-slate-500 shadow-sm">{icon}</div>
      <div className="min-w-0">
        <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">{label}</div>
        <div className="mt-1 text-base font-semibold leading-tight text-slate-900">{value}</div>
      </div>
    </div>
  );
}

function timeControlIcon(category: string) {
  if (category === "blitz") return <Zap className="h-4 w-4" />;
  if (category === "rapid") return <Clock3 className="h-4 w-4" />;
  return <Turtle className="h-4 w-4" />;
}

function formatTournamentDates(startDate: string, endDate: string, rounds?: { scheduled_at?: string | null }[]) {
  if (startDate === endDate) {
    return formatMonthDay(startDate);
  }

  return `${formatMonthDay(startDate)} - ${formatMonthDay(endDate)}`;
}

function formatMonthDay(value: string) {
  const date = new Date(`${value}T00:00:00`);
  const month = new Intl.DateTimeFormat("it-IT", { month: "short" }).format(date).replace(".", "");
  const day = new Intl.DateTimeFormat("it-IT", { day: "2-digit" }).format(date);
  return `${month} ${day}`;
}

function FederationCell({ federation }: { federation?: string | null }) {
  const flagUrl = getFederationFlagUrl(federation);
  return (
    <div className="flex items-center gap-2">
      {flagUrl ? <img alt={federation ?? "Federation"} className="h-4 w-5 rounded-sm object-cover" src={flagUrl} /> : null}
      <span>{federation ?? "-"}</span>
    </div>
  );
}

function getStandingRating(entry: { rating?: number | null; rapid_rating?: number | null; blitz_rating?: number | null }, category: string) {
  if (category === "blitz") return entry.blitz_rating ?? entry.rating ?? "-";
  if (category === "rapid") return entry.rapid_rating ?? entry.rating ?? "-";
  return entry.rating ?? "-";
}

function renderTieBreakValue(
  entry: {
    buchholz_cut1: number;
    buchholz: number;
    sonneborn_berger: number;
    played_games: number;
    wins: number;
    black_wins: number;
    rating?: number | null;
    rapid_rating?: number | null;
    blitz_rating?: number | null;
  },
  criterion: string,
  category: string,
) {
  if (criterion === "buchholz_cut1") return formatScore(entry.buchholz_cut1);
  if (criterion === "buchholz") return formatScore(entry.buchholz);
  if (criterion === "sonneborn_berger") return formatScore(entry.sonneborn_berger);
  if (criterion === "played_games") return entry.played_games;
  if (criterion === "rating") return getStandingRating(entry, category);
  if (criterion === "wins_black") return `${entry.wins}/${entry.black_wins}`;
  if (criterion === "direct_encounter") return "DE";
  return "-";
}

function renderTeamTieBreakValue(
  entry: {
    individual_points: number;
    head_to_head_applies: boolean;
    head_to_head_match_points: number;
    head_to_head_individual_points: number;
    weighted_sonneborn: number;
  },
  criterion: string,
  tournamentType?: string,
) {
  if (criterion === "individual_points") return formatScore(entry.individual_points);
  if (criterion === "head_to_head") {
    if (!entry.head_to_head_applies) return "-";
    if (tournamentType === "quadriglia") return formatScore(entry.head_to_head_match_points);
    return `${formatScore(entry.head_to_head_match_points)} / ${formatScore(entry.head_to_head_individual_points)}`;
  }
  if (criterion === "weighted_sonneborn") return formatScore(entry.weighted_sonneborn);
  return "-";
}

function formatScore(value: number) {
  return Number.isInteger(value) ? String(value) : value.toFixed(1).replace(/\.0$/, "");
}

function formatEloChange(value?: number | null) {
  if (value == null) return "-";
  if (value === 0) return "0";
  return value > 0 ? `+${formatScore(value)}` : formatScore(value);
}

function PlayerAvailabilityDialog({
  player,
  roundsCount,
  onClose,
  onToggleAvailability,
  onToggleStatus,
}: {
  player: TournamentPlayer;
  roundsCount: number;
  onClose: () => void;
  onToggleAvailability: (roundNumber: number, isAvailable: boolean) => void;
  onToggleStatus: () => void;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4" onClick={onClose}>
      <Card className="w-full max-w-lg" onClick={(event) => event.stopPropagation()}>
        <CardHeader>
          <CardTitle>{player.full_name}</CardTitle>
          <CardDescription>Disponibilità per turno e stato del giocatore nel torneo.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-4 gap-2 sm:grid-cols-6 lg:grid-cols-8">
            {Array.from({ length: roundsCount }, (_, index) => {
              const roundNumber = index + 1;
              const isAvailable = player.availability_by_round[index] ?? true;
              return (
                <button
                  key={roundNumber}
                  type="button"
                  className={`flex h-10 w-10 items-center justify-center rounded-md border font-semibold ${isAvailable ? "border-slate-300 bg-white text-slate-900 text-sm" : "border-red-300 bg-slate-100 text-red-600 text-xl leading-none"}`}
                  onClick={() => onToggleAvailability(roundNumber, isAvailable)}
                  title={`Turno ${roundNumber}`}
                >
                  {isAvailable ? roundNumber : "×"}
                </button>
              );
            })}
          </div>
          <div className="flex items-center justify-between gap-3">
            <Button variant="destructive" onClick={onToggleStatus} disabled={!player.is_active}>
              Ritira dal torneo
            </Button>
            <Button variant="outline" onClick={onClose}>
              Chiudi
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function readErrorMessage(error: unknown) {
  if (isAxiosError(error)) {
    if (typeof error.response?.data?.message === "string") return error.response.data.message;
    return typeof error.response?.data?.detail === "string" ? error.response.data.detail : error.message;
  }
  if (error instanceof Error) return error.message;
  return "Si è verificato un errore inatteso.";
}
