import { useEffect, useRef, useState } from "react";
import type { Pairing, PairingResult, Round, StandingEntry, TournamentPlayer, TournamentType } from "@/api/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getFederationFlagUrl } from "@/lib/federationFlags";

type Props = {
  canManage: boolean;
  rounds: Round[];
  standings: StandingEntry[];
  players: TournamentPlayer[];
  tournamentType: TournamentType;
  category: string;
  totalRounds: number;
  nextRoundNumber: number;
  registrationClosed: boolean;
  canGenerateNextRound: boolean;
  onGenerateRound: () => void;
  showConcludeTournament: boolean;
  canConcludeTournament: boolean;
  isTournamentConcluded: boolean;
  onConcludeTournament: () => void;
  onDeleteLatestRound: () => void;
  isGenerating?: boolean;
  isDeleting?: boolean;
  onResultChange: (pairingId: number, result: PairingResult, currentResult: PairingResult) => void;
};

const results: PairingResult[] = ["1-0", "0-1", "1/2-1/2", "1-0F", "0-1F", "0F-0F", "1F-1F"];

export function RoundsPanel({
  canManage,
  rounds,
  standings,
  players,
  tournamentType,
  category,
  totalRounds,
  nextRoundNumber,
  registrationClosed,
  canGenerateNextRound,
  onGenerateRound,
  showConcludeTournament,
  canConcludeTournament,
  isTournamentConcluded,
  onConcludeTournament,
  onDeleteLatestRound,
  isGenerating = false,
  isDeleting = false,
  onResultChange,
}: Props) {
  const [selectedRoundId, setSelectedRoundId] = useState<number | null>(rounds[rounds.length - 1]?.id ?? null);
  const [expandedPairingId, setExpandedPairingId] = useState<number | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    setSelectedRoundId((current) => (rounds.some((round) => round.id === current) ? current : (rounds[rounds.length - 1]?.id ?? null)));
  }, [rounds]);

  useEffect(() => {
    setSelectedRoundId(rounds[rounds.length - 1]?.id ?? null);
  }, [rounds.length]);

  useEffect(() => {
    setExpandedPairingId(null);
  }, [selectedRoundId]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (!containerRef.current?.contains(event.target as Node)) {
        setExpandedPairingId(null);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const selectedRound = rounds.find((round) => round.id === selectedRoundId) ?? rounds[rounds.length - 1];
  const selectedRoundIndex = rounds.findIndex((round) => round.id === selectedRound?.id);
  const latestRound = rounds[rounds.length - 1];
  const isLatestRoundSelected = selectedRound?.id === latestRound?.id;
  const standingsByPlayer = new Map(standings.map((entry) => [entry.player_id, entry]));
  const playersById = new Map(players.map((player) => [player.player_id, player]));
  const roundActionLabel = showConcludeTournament ? "Concludi torneo" : `Genera turno ${nextRoundNumber}`;
  const roundActionPendingLabel = showConcludeTournament ? "Conclusione torneo..." : `Generazione turno ${nextRoundNumber}...`;

  if (!selectedRound) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Turni</CardTitle>
        </CardHeader>
        <CardContent className="pt-0">
          {canManage ? (
            <Button
              onClick={showConcludeTournament ? onConcludeTournament : onGenerateRound}
              disabled={isTournamentConcluded || !registrationClosed || (showConcludeTournament ? !canConcludeTournament : !canGenerateNextRound) || isGenerating}
            >
              {isGenerating ? roundActionPendingLabel : roundActionLabel}
            </Button>
          ) : <div className="text-sm text-[var(--muted-foreground)]">Nessun turno ancora pubblicato.</div>}
        </CardContent>
      </Card>
    );
  }

  return (
    <div ref={containerRef}>
      <Card>
        <CardHeader>
          <CardTitle>Turni</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={selectedRoundIndex <= 0}
              onClick={() => setSelectedRoundId(rounds[selectedRoundIndex - 1]?.id ?? null)}
            >
              Prec.
            </Button>
            <div className="min-w-24 text-center text-sm font-medium">Turno {selectedRound.number}</div>
            <Button
              variant="outline"
              size="sm"
              disabled={selectedRoundIndex >= rounds.length - 1}
              onClick={() => setSelectedRoundId(rounds[selectedRoundIndex + 1]?.id ?? null)}
            >
              Succ.
            </Button>
          </div>
          {canManage ? (
            <div className="flex flex-wrap gap-2">
              <Button
                onClick={showConcludeTournament ? onConcludeTournament : onGenerateRound}
                disabled={isTournamentConcluded || !registrationClosed || (showConcludeTournament ? !canConcludeTournament : !canGenerateNextRound) || isGenerating}
              >
                {isGenerating ? roundActionPendingLabel : roundActionLabel}
              </Button>
              <Button variant="destructive" onClick={onDeleteLatestRound} disabled={!isLatestRoundSelected || isDeleting}>
                {isDeleting ? "Eliminazione..." : `Elimina turno ${latestRound.number}`}
              </Button>
            </div>
          ) : null}
        </div>
        <div className="space-y-3">
              {tournamentType === "team"
            ? renderTeamMatches({
                pairings: selectedRound.pairings,
                playersById,
                standingsByPlayer,
                category,
                isLatestRoundSelected,
                expandedPairingId,
                setExpandedPairingId,
                onResultChange,
              })
            : selectedRound.pairings.map((pairing) => {
            const whitePlayer = playersById.get(pairing.white_player_id);
            const blackPlayer = pairing.black_player_id ? playersById.get(pairing.black_player_id) : undefined;
            const whiteStanding = standingsByPlayer.get(pairing.white_player_id);
            const blackStanding = pairing.black_player_id ? standingsByPlayer.get(pairing.black_player_id) : undefined;

            return (
              <Card
                key={pairing.id}
                 className={`border border-[var(--border)] ${canManage && isLatestRoundSelected && !pairing.is_bye ? "cursor-pointer" : "cursor-default"}`}
                 onClick={() => {
                   if (!canManage || !isLatestRoundSelected || pairing.is_bye) return;
                   setExpandedPairingId((current) => (current === pairing.id ? null : pairing.id));
                 }}
              >
                <CardContent className="space-y-3 py-3">
                  <div className="grid gap-2 lg:grid-cols-[56px_1fr_120px_1fr] lg:items-stretch">
                    <div className="flex items-center justify-center rounded-xl border bg-[var(--muted)] text-sm font-semibold">
                      {pairing.board_number}
                    </div>
                    <PlayerMatchCard player={whitePlayer} standing={whiteStanding} category={category} />
                    <div className="flex items-center justify-center rounded-xl border bg-[var(--muted)] px-3 text-center text-sm font-semibold">
                      {renderCompactResult(pairing)}
                    </div>
                    <PlayerMatchCard player={blackPlayer} standing={blackStanding} category={category} isBye={pairing.is_bye} />
                  </div>
                  {!pairing.is_bye && canManage && isLatestRoundSelected && expandedPairingId === pairing.id ? (
                    <div className="flex flex-wrap justify-center gap-2 pt-1">
                      {results.map((result) => (
                        <Button
                          key={result}
                          variant={pairing.result === result ? "default" : "outline"}
                          size="sm"
                          onClick={(event) => {
                            event.stopPropagation();
                            onResultChange(pairing.id, result, pairing.result);
                            setExpandedPairingId(null);
                          }}
                        >
                          {result}
                        </Button>
                      ))}
                    </div>
                  ) : null}
                </CardContent>
              </Card>
            );
          })}
        </div>
        </CardContent>
      </Card>
    </div>
  );
}

function PlayerMatchCard({
  player,
  standing,
  category,
  isBye = false,
  pieceColor,
}: {
  player?: TournamentPlayer;
  standing?: StandingEntry;
  category: string;
  isBye?: boolean;
  pieceColor?: "white" | "black";
}) {
  if (isBye && !player) {
    return (
      <div className="rounded-xl border bg-[var(--muted)] px-3 py-2 text-sm text-[var(--muted-foreground)] flex items-center justify-center">BYE</div>
    );
  }

  if (!player) {
    return null;
  }

  const rating =
    category === "blitz" ? (player.blitz_rating ?? player.rating) : category === "rapid" ? (player.rapid_rating ?? player.rating) : player.rating;

  return (
    <div className="rounded-xl border bg-white px-3 py-2 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            {pieceColor ? (
              <span className={`h-3 w-3 rounded-sm border ${pieceColor === "white" ? "border-slate-400 bg-white" : "border-slate-700 bg-slate-900"}`} />
            ) : null}
            <div className="truncate text-sm font-semibold">{player.full_name}</div>
          </div>
          <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-[var(--muted-foreground)]">
            <span>N°{player.seed_number ?? "-"}</span>
            <span className="font-medium text-[var(--foreground)]">{rating ?? "-"}</span>
            <span>{formatScore(standing?.points ?? 0)} pt</span>
          </div>
        </div>
        <div className="text-right text-xs">
          <div className="flex items-center justify-end gap-2 text-[var(--muted-foreground)]">
            <FederationFlag federation={player.federation} />
            <span>{player.federation ?? "-"}</span>
          </div>
          <div className="mt-1 text-[var(--muted-foreground)]">b.y. {player.birth_year ?? "-"}</div>
        </div>
      </div>
    </div>
  );
}

function FederationFlag({ federation }: { federation?: string | null }) {
  const countryCode = getFederationFlagUrl(federation);
  if (!countryCode) return null;
  return <span className={`fi fi-${countryCode} fis rounded-sm`} />;
}

function renderCompactResult(pairing: { result: PairingResult; is_bye: boolean }) {
  if (pairing.is_bye) return "1-bye";
  if (pairing.result === "1-0") return "1-0";
  if (pairing.result === "0-1") return "0-1";
  if (pairing.result === "1/2-1/2") return "1/2-1/2";
  if (pairing.result === "1-0F") return "1-0F";
  if (pairing.result === "0-1F") return "0-1F";
  if (pairing.result === "0F-0F") return "0F-0F";
  if (pairing.result === "1F-1F") return "1F-1F";
  return "...";
}

function renderTeamMatches({
  pairings,
  playersById,
  standingsByPlayer,
  category,
  isLatestRoundSelected,
  expandedPairingId,
  setExpandedPairingId,
  onResultChange,
}: {
  pairings: Pairing[];
  playersById: Map<number, TournamentPlayer>;
  standingsByPlayer: Map<number, StandingEntry>;
  category: string;
  isLatestRoundSelected: boolean;
  expandedPairingId: number | null;
  setExpandedPairingId: (value: number | null | ((current: number | null) => number | null)) => void;
  onResultChange: (pairingId: number, result: PairingResult, currentResult: PairingResult) => void;
}) {
  const matches = new Map<number, Pairing[]>();
  pairings.forEach((pairing) => {
    const key = pairing.match_number ?? pairing.board_number;
    matches.set(key, [...(matches.get(key) ?? []), pairing]);
  });

  return Array.from(matches.entries())
    .sort((left, right) => left[0] - right[0])
    .map(([matchNumber, matchPairings]) => {
    const sortedPairings = [...matchPairings].sort((left, right) => left.board_number - right.board_number);
    const whiteTeamName = sortedPairings[0]?.white_team_name ?? "Squadra A";
    const blackTeamName = sortedPairings[0]?.black_team_name ?? "Squadra B";
    const whiteScore = sortedPairings.reduce((total, pairing) => total + pairing.white_points, 0);
    const blackScore = sortedPairings.reduce((total, pairing) => total + pairing.black_points, 0);

    return (
      <Card key={matchNumber} className="border border-[var(--border)]">
        <CardContent className="py-4">
          <div className="grid gap-3 lg:grid-cols-[56px_1fr] lg:items-stretch">
            <div className="flex h-full items-center justify-center self-stretch rounded-xl border bg-[var(--muted)] text-sm font-semibold">
              {matchNumber}
            </div>
            <div className="space-y-3">
              <div className="rounded-xl border bg-[var(--muted)] px-4 py-3 text-center text-base font-semibold">
                <div className="grid gap-3 lg:grid-cols-[1.4fr_180px_1.4fr] lg:items-stretch">
                  <div className="rounded-xl border bg-white px-3 py-3 shadow-sm text-left">{whiteTeamName}</div>
                  <div className="flex items-center justify-center rounded-xl border bg-[var(--muted)] px-3 py-3 text-center">
                    {formatScore(whiteScore)} - {formatScore(blackScore)}
                  </div>
                  <div className="rounded-xl border bg-white px-3 py-3 shadow-sm text-right">{blackTeamName}</div>
                </div>
              </div>
              {sortedPairings.map((pairing) => {
                const whitePlayer = playersById.get(pairing.white_player_id);
                const whiteStanding = standingsByPlayer.get(pairing.white_player_id);
                const blackPlayer = pairing.black_player_id ? playersById.get(pairing.black_player_id) : undefined;
                const blackStanding = pairing.black_player_id ? standingsByPlayer.get(pairing.black_player_id) : undefined;

                return (
                  <div key={pairing.id} className="grid gap-3 lg:grid-cols-[1.4fr_180px_1.4fr] lg:items-stretch">
                    <PlayerMatchCard player={whitePlayer} standing={whiteStanding} category={category} pieceColor={pairing.board_number % 2 === 1 ? "white" : "black"} />
                    <div
                      className={`rounded-xl border bg-[var(--muted)] px-3 py-3 text-center ${!pairing.is_bye && isLatestRoundSelected ? "cursor-pointer" : "cursor-default"}`}
                      onClick={() => {
                        if (!isLatestRoundSelected || pairing.is_bye) return;
                        setExpandedPairingId((current) => (current === pairing.id ? null : pairing.id));
                      }}
                    >
                      <div className="text-base font-semibold">{renderCompactResult(pairing)}</div>
                      {!pairing.is_bye && isLatestRoundSelected && expandedPairingId === pairing.id ? (
                        <div className="mt-2 flex flex-wrap justify-center gap-1">
                          {results.map((result) => (
                            <Button
                              key={result}
                              variant={pairing.result === result ? "default" : "outline"}
                              size="sm"
                              onClick={(event) => {
                                event.stopPropagation();
                                onResultChange(pairing.id, result, pairing.result);
                                setExpandedPairingId(null);
                              }}
                            >
                              {result}
                            </Button>
                          ))}
                        </div>
                      ) : null}
                    </div>
                    <PlayerMatchCard player={blackPlayer} standing={blackStanding} category={category} isBye={pairing.is_bye} pieceColor={pairing.board_number % 2 === 1 ? "black" : "white"} />
                  </div>
                );
              })}
            </div>
          </div>
        </CardContent>
      </Card>
    );
  });
}

function formatScore(value: number) {
  return Number.isInteger(value) ? String(value) : value.toFixed(1).replace(/\.0$/, "");
}
