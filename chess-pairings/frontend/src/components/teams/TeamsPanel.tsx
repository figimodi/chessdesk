import { useEffect, useMemo, useState } from "react";
import type { Team, TournamentPlayer } from "@/api/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Item, ItemActions, ItemContent } from "@/components/ui/item";
import { getFederationFlagUrl } from "@/lib/federationFlags";

type Props = {
  canManage: boolean;
  teams: Team[];
  players: TournamentPlayer[];
  roundsCount: number;
  boardsPerMatch: number;
  category: string;
  onCreateTeam: (name: string) => void;
  onDeleteTeam: (teamId: number) => void;
  onAssignMember: (teamId: number, playerId: number) => void;
  onRemoveMember: (teamId: number, playerId: number) => void;
  onReorderMembers: (teamId: number, playerIds: number[]) => void;
  onToggleTeamAvailability: (teamId: number, roundNumber: number, isAvailable: boolean) => void;
  onToggleTeamStatus: (teamId: number, isActive: boolean) => void;
  onToggleTeamLineup: (teamId: number, playerId: number, roundNumber: number, isSelected: boolean) => void;
};

type DragPayload = { kind: "unassigned"; playerId: number } | { kind: "team-member"; playerId: number; fromTeamId: number };

export function TeamsPanel({
  canManage,
  teams,
  players,
  roundsCount,
  boardsPerMatch,
  category,
  onCreateTeam,
  onDeleteTeam,
  onAssignMember,
  onRemoveMember,
  onReorderMembers,
  onToggleTeamAvailability,
  onToggleTeamStatus,
  onToggleTeamLineup,
}: Props) {
  const pageSize = 10;
  const [teamName, setTeamName] = useState("");
  const [selectedTeamId, setSelectedTeamId] = useState<number | null>(null);
  const [dragPayload, setDragPayload] = useState<DragPayload | null>(null);
  const [unassignedPage, setUnassignedPage] = useState(1);

  const sortedTeams = useMemo(() => [...teams].sort(compareTeamsByStrength(category)), [category, teams]);
  const unassignedPlayers = useMemo(
    () => players.filter((player) => player.team_id == null).sort((left, right) => comparePlayerStrength(left, right, category)),
    [category, players],
  );
  const totalPages = Math.max(1, Math.ceil(unassignedPlayers.length / pageSize));
  const safePage = Math.min(unassignedPage, totalPages);
  const paginatedUnassignedPlayers = unassignedPlayers.slice((safePage - 1) * pageSize, safePage * pageSize);
  const selectedTeam = selectedTeamId == null ? null : (teams.find((team) => team.id === selectedTeamId) ?? null);

  useEffect(() => {
    setUnassignedPage((current) => Math.min(current, totalPages));
  }, [totalPages]);

  return (
    <div className="space-y-4">
      {selectedTeam ? (
        <TeamDialog
          canManage={canManage}
          key={selectedTeam.id}
          team={selectedTeam}
          roundsCount={roundsCount}
          boardsPerMatch={boardsPerMatch}
          onClose={() => setSelectedTeamId(null)}
          onDeleteTeam={onDeleteTeam}
          onToggleTeamAvailability={onToggleTeamAvailability}
          onToggleTeamStatus={onToggleTeamStatus}
          onToggleTeamLineup={onToggleTeamLineup}
        />
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle>Nuova squadra</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-3">
          {canManage ? (
            <>
              <Input className="max-w-sm" placeholder="Nome squadra" value={teamName} onChange={(event) => setTeamName(event.target.value)} />
              <Button
                onClick={() => {
                  const trimmed = teamName.trim();
                  if (!trimmed) return;
                  onCreateTeam(trimmed);
                  setTeamName("");
                }}
              >
                Crea squadra
              </Button>
            </>
          ) : (
            <div className="text-sm text-[var(--muted-foreground)]">Solo i proprietari del torneo possono modificare le squadre.</div>
          )}
        </CardContent>
      </Card>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,2fr)_minmax(320px,1fr)]">
        <div className="space-y-4">
          {canManage ? <div className="text-xs text-[var(--muted-foreground)]">Trascina i giocatori per riordinarli o spostarli tra le squadre.</div> : null}
          {sortedTeams.map((team) => (
            <TeamRosterCard
              key={team.id}
              canManage={canManage}
              team={team}
              category={category}
              dragPayload={dragPayload}
              onOpen={() => setSelectedTeamId(team.id)}
              onAssignMember={onAssignMember}
              onReorderMembers={onReorderMembers}
              onRemoveMember={onRemoveMember}
              setDragPayload={setDragPayload}
            />
          ))}
          {!sortedTeams.length ? (
            <Card>
              <CardContent className="py-6 text-sm text-[var(--muted-foreground)]">Nessuna squadra creata.</CardContent>
            </Card>
          ) : null}
        </div>

        <Card
          className="self-start xl:sticky xl:top-4"
          onDragOver={(event) => {
            if (!canManage || !dragPayload) return;
            event.preventDefault();
          }}
          onDrop={() => {
            if (!canManage || !dragPayload || dragPayload.kind !== "team-member") return;
            onRemoveMember(dragPayload.fromTeamId, dragPayload.playerId);
            setDragPayload(null);
          }}
        >
          <CardHeader>
            <CardTitle>Giocatori non assegnati</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {paginatedUnassignedPlayers.map((player) => (
              <DraggablePlayerRow
                key={player.player_id}
                className={dragPayload?.playerId === player.player_id ? "opacity-60" : ""}
                label={player.full_name}
                seedNumber={player.seed_number}
                federation={player.federation}
                rating={getPlayerRating(player, category)}
                birthYear={player.birth_year}
                draggable={canManage}
                onDragStart={() => setDragPayload({ kind: "unassigned", playerId: player.player_id })}
                onDragEnd={() => setDragPayload(null)}
              />
            ))}
            {!unassignedPlayers.length ? <div className="text-sm text-[var(--muted-foreground)]">Tutti i giocatori sono assegnati.</div> : null}
            {unassignedPlayers.length > pageSize ? (
              <div className="flex items-center justify-between gap-3 pt-2 text-sm">
                <div className="text-[var(--muted-foreground)]">
                  Pagina {safePage} di {totalPages}
                </div>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" disabled={safePage <= 1} onClick={() => setUnassignedPage((current) => Math.max(1, current - 1))}>
                    Prec.
                  </Button>
                  <Button variant="outline" size="sm" disabled={safePage >= totalPages} onClick={() => setUnassignedPage((current) => Math.min(totalPages, current + 1))}>
                    Succ.
                  </Button>
                </div>
              </div>
            ) : null}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function TeamRosterCard({
  canManage,
  team,
  category,
  dragPayload,
  onOpen,
  onAssignMember,
  onReorderMembers,
  onRemoveMember,
  setDragPayload,
}: {
  canManage: boolean;
  team: Team;
  category: string;
  dragPayload: DragPayload | null;
  onOpen: () => void;
  onAssignMember: (teamId: number, playerId: number) => void;
  onReorderMembers: (teamId: number, playerIds: number[]) => void;
  onRemoveMember: (teamId: number, playerId: number) => void;
  setDragPayload: (payload: DragPayload | null) => void;
}) {
  const averageRating = computeAverageRating(team, category);
  const highestRating = computeHighestRating(team, category);

  return (
    <Card
      className={canManage ? "cursor-pointer" : "cursor-default"}
      onClick={onOpen}
      onDragOver={(event) => {
        if (!canManage || !dragPayload) return;
        event.preventDefault();
      }}
      onDrop={() => {
        if (!canManage || !dragPayload) return;
        if (dragPayload.kind === "team-member" && dragPayload.fromTeamId === team.id) return;
        onAssignMember(team.id, dragPayload.playerId);
        setDragPayload(null);
      }}
    >
      <CardHeader>
        <div className="flex items-center justify-between gap-3">
          <div>
            <CardTitle className="text-lg">{team.name}</CardTitle>
            <div className="mt-1 text-sm text-[var(--muted-foreground)]">
              Elo medio {averageRating ?? "-"} · Elo max {highestRating ?? "-"} · {team.members_count} giocatori
            </div>
          </div>
          {!team.is_active ? <div className="text-sm font-medium text-red-600">Ritirata</div> : null}
        </div>
      </CardHeader>
      <CardContent className="space-y-2" onClick={(event) => event.stopPropagation()}>
        {team.members.map((member, index) => (
          <Item
            key={member.player_id}
            className={dragPayload?.playerId === member.player_id ? "opacity-60" : ""}
            draggable={canManage}
            onDragStart={() => setDragPayload({ kind: "team-member", playerId: member.player_id, fromTeamId: team.id })}
            onDragEnd={() => setDragPayload(null)}
            onDragOver={(event) => {
              if (!canManage || !dragPayload) return;
              event.preventDefault();
            }}
            onDrop={() => {
              if (!canManage || !dragPayload) return;

              if (dragPayload.kind === "team-member" && dragPayload.fromTeamId === team.id) {
                if (dragPayload.playerId === member.player_id) return;

                const orderedIds = team.members.map((entry) => entry.player_id);
                const fromIndex = orderedIds.indexOf(dragPayload.playerId);
                const toIndex = orderedIds.indexOf(member.player_id);
                if (fromIndex < 0 || toIndex < 0 || fromIndex === toIndex) return;

                const reordered = [...orderedIds];
                const [moved] = reordered.splice(fromIndex, 1);
                reordered.splice(toIndex, 0, moved);
                onReorderMembers(team.id, reordered);
                setDragPayload(null);
                return;
              }

              onAssignMember(team.id, dragPayload.playerId);
              setDragPayload(null);
            }}
          >
            <ItemContent className="flex items-center gap-2">
              <div className="w-8 font-medium">{member.team_board_order ?? index + 1}</div>
              <DraggablePlayerRow
                className="flex-1 border-0 p-0"
                label={member.full_name}
                seedNumber={member.seed_number}
                federation={member.federation}
                rating={getTeamMemberRating(member, category)}
                birthYear={member.birth_year}
                draggable={false}
                onDragStart={() => undefined}
                onDragEnd={() => undefined}
              />
            </ItemContent>
            <ItemActions>
              {canManage ? (
                <Button variant="destructive" size="sm" onClick={() => onRemoveMember(team.id, member.player_id)}>
                  Rimuovi
                </Button>
              ) : null}
            </ItemActions>
          </Item>
        ))}
        {!team.members.length ? (
          <div className="text-sm text-[var(--muted-foreground)]">Trascina qui i giocatori dalla colonna di destra.</div>
        ) : null}
      </CardContent>
    </Card>
  );
}

function DraggablePlayerRow({
  label,
  seedNumber,
  federation,
  rating,
  birthYear,
  draggable = true,
  onDragStart,
  onDragEnd,
  className = "",
}: {
  label: string;
  seedNumber?: number | null;
  federation?: string | null;
  rating?: number | null;
  birthYear?: number | null;
  draggable?: boolean;
  onDragStart: () => void;
  onDragEnd: () => void;
  className?: string;
}) {
  const flagUrl = getFederationFlagUrl(federation);

  return (
    <div
      draggable={draggable}
      onDragStart={onDragStart}
      onDragEnd={onDragEnd}
      className={`rounded-xl border bg-white px-3 py-2 shadow-sm ${className}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="truncate text-sm font-semibold">{label}</div>
          <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-[var(--muted-foreground)]">
            <span>{seedNumber ? `N° ${seedNumber}` : "-"}</span>
            <span className="font-medium text-[var(--foreground)]">{rating ?? ""}</span>
          </div>
        </div>
        <div className="text-right text-xs">
          <div className="flex items-center justify-end gap-2 text-[var(--muted-foreground)]">
            {flagUrl ? <img alt={federation ?? "Federation"} className="h-4 w-5 rounded-sm object-cover" src={flagUrl} /> : null}
            <span>{federation ?? ""}</span>
          </div>
          <div className="mt-1 text-[var(--muted-foreground)]">{birthYear ? `b.y. ${birthYear}` : ""}</div>
        </div>
      </div>
    </div>
  );
}

function TeamDialog({
  canManage,
  team,
  roundsCount,
  boardsPerMatch,
  onClose,
  onDeleteTeam,
  onToggleTeamAvailability,
  onToggleTeamStatus,
  onToggleTeamLineup,
}: {
  canManage: boolean;
  team: Team;
  roundsCount: number;
  boardsPerMatch: number;
  onClose: () => void;
  onDeleteTeam: (teamId: number) => void;
  onToggleTeamAvailability: (teamId: number, roundNumber: number, isAvailable: boolean) => void;
  onToggleTeamStatus: (teamId: number, isActive: boolean) => void;
  onToggleTeamLineup: (teamId: number, playerId: number, roundNumber: number, isSelected: boolean) => void;
}) {
  const autoSelectAllMembers = team.members.length <= boardsPerMatch;
  const selectedCountsByRound = Array.from({ length: roundsCount }, (_, index) =>
    team.members.reduce((total, member) => total + ((member.selected_by_round[index] ?? false) ? 1 : 0), 0),
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4" onClick={onClose}>
      <Card className="w-full max-w-6xl" onClick={(event) => event.stopPropagation()}>
        <CardHeader>
          <div className="flex items-center justify-between gap-3">
            <CardTitle>{team.name}</CardTitle>
            {canManage ? (
              <div className="flex gap-2">
                <Button variant="destructive" onClick={() => onToggleTeamStatus(team.id, false)} disabled={!team.is_active}>
                  Ritira squadra
                </Button>
                <Button variant="destructive" onClick={() => onDeleteTeam(team.id)}>
                  Elimina squadra
                </Button>
              </div>
            ) : null}
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          <div>
            <div className="mb-2 text-sm font-medium">Disponibilita squadra</div>
            <div className="flex flex-wrap gap-2">
              {Array.from({ length: roundsCount }, (_, index) => {
                const roundNumber = index + 1;
                const isAvailable = team.availability_by_round[index] ?? true;
                return (
                  <button
                    key={roundNumber}
                    type="button"
                    className={`flex h-10 w-10 items-center justify-center rounded-md border font-semibold ${isAvailable ? "border-slate-300 bg-white text-slate-900 text-sm" : "border-red-300 bg-slate-100 text-red-600 text-xl leading-none"}`}
                    onClick={() => onToggleTeamAvailability(team.id, roundNumber, !isAvailable)}
                    disabled={!canManage}
                  >
                    {isAvailable ? roundNumber : "×"}
                  </button>
                );
              })}
            </div>
          </div>

          <div>
            <div className="mb-2 text-sm font-medium">Formazione per turno</div>
            <div className="mb-3 text-xs text-[var(--muted-foreground)]">
              Seleziona i giocatori schierati per ogni turno. Obiettivo: {boardsPerMatch} giocatori per turno.
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full border-separate border-spacing-y-2 text-sm">
                <thead>
                  <tr className="text-left text-[var(--muted-foreground)]">
                    <th className="px-2">Sc.</th>
                    <th className="px-2">Giocatore</th>
                    {Array.from({ length: roundsCount }, (_, index) => (
                      <th key={index} className="px-2 text-center">
                        T{index + 1}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {team.members.map((member, memberIndex) => (
                    <tr key={member.player_id} className="rounded-xl border bg-white">
                      <td className="px-2 py-2">{member.team_board_order ?? memberIndex + 1}</td>
                      <td className="px-2 py-2 min-w-56">{member.full_name}</td>
                      {Array.from({ length: roundsCount }, (_, index) => {
                        const roundNumber = index + 1;
                        const isSelected = member.selected_by_round[index] ?? false;
                        const isDisabled = autoSelectAllMembers || (!isSelected && selectedCountsByRound[index] >= boardsPerMatch);
                        return (
                          <td key={roundNumber} className="px-2 py-2 text-center">
                            <button
                              type="button"
                              className={`h-9 w-9 rounded-md border font-semibold ${isSelected ? "border-emerald-300 bg-emerald-100 text-emerald-700 text-sm" : "border-slate-300 bg-white text-slate-500"}`}
                              onClick={() => {
                                if (isDisabled && !isSelected) return;
                                if (autoSelectAllMembers) return;
                                onToggleTeamLineup(team.id, member.player_id, roundNumber, !isSelected);
                              }}
                              disabled={!canManage || (isDisabled && !isSelected)}
                            >
                              {isSelected ? "✓" : "-"}
                            </button>
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="flex justify-end">
            <Button variant="outline" onClick={onClose}>
              Chiudi
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function compareTeamsByStrength(category: string) {
  return (left: Team, right: Team) => {
    const leftAverage = computeAverageRating(left, category) ?? 0;
    const rightAverage = computeAverageRating(right, category) ?? 0;
    const leftMax = computeHighestRating(left, category) ?? 0;
    const rightMax = computeHighestRating(right, category) ?? 0;
    return rightAverage - leftAverage || rightMax - leftMax || left.name.localeCompare(right.name);
  };
}

function computeAverageRating(team: Team, category: string) {
  const ratings = team.members.map((member) => getTeamMemberRating(member, category)).filter((value): value is number => value != null);
  if (!ratings.length) return null;
  return Math.round(ratings.reduce((total, value) => total + value, 0) / ratings.length);
}

function computeHighestRating(team: Team, category: string) {
  const ratings = team.members.map((member) => getTeamMemberRating(member, category)).filter((value): value is number => value != null);
  return ratings.length ? Math.max(...ratings) : null;
}

function comparePlayerStrength(left: TournamentPlayer, right: TournamentPlayer, category: string) {
  const leftRating = getPlayerRating(left, category) ?? 0;
  const rightRating = getPlayerRating(right, category) ?? 0;
  return rightRating - leftRating || left.full_name.localeCompare(right.full_name);
}

function getPlayerRating(player: TournamentPlayer, category: string) {
  if (category === "blitz") return player.blitz_rating ?? player.rating ?? null;
  if (category === "rapid") return player.rapid_rating ?? player.rating ?? null;
  return player.initial_rating ?? player.rating ?? null;
}

function getTeamMemberRating(member: Team["members"][number], category: string) {
  if (category === "blitz") return member.blitz_rating ?? member.rating ?? null;
  if (category === "rapid") return member.rapid_rating ?? member.rating ?? null;
  return member.rating ?? null;
}
