import { useEffect, useMemo, useState } from "react";
import { isAxiosError } from "axios";
import { ArrowDown, ArrowUp, Search, Trash2, UserPlus } from "lucide-react";
import { useFideSearch } from "@/api/hooks/players";
import {
  useCreatePublicTeamRegistration,
  useJoinPublicTeamRegistration,
  usePublicTournamentRegistration,
  useTournament,
} from "@/api/hooks/tournaments";
import type {
  FidePlayer,
  PublicTeamRegistrationCreateResponse,
  TournamentDetail,
  TournamentListItem,
  TournamentPublicRegistration,
} from "@/api/types";
import { getFederationFlagUrl } from "@/lib/federationFlags";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

type Props = {
  onClose: () => void;
  tournament: Pick<TournamentListItem, "id" | "name" | "time_control_category" | "is_registration_closed">;
};

type DraftTeammate = {
  id: string;
  label: string;
  kind: "existing" | "fide" | "manual";
  playerId?: number;
  fideId?: string;
  firstName?: string;
  lastName?: string;
};

export function TournamentRegistrationDialog({ onClose, tournament }: Props) {
  const { data: tournamentDetail } = useTournament(String(tournament.id));

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4" onClick={onClose}>
      <Card className="flex max-h-[85vh] w-full max-w-4xl flex-col overflow-hidden" onClick={(event) => event.stopPropagation()}>
        <CardHeader>
          <CardTitle>Iscriviti a {tournament.name}</CardTitle>
          <CardDescription>
            {tournamentDetail?.type === "team"
              ? "Per i tornei a squadre puoi creare una nuova squadra, unirti con PIN o iscriverti senza squadra."
              : "Puoi cercarti nel catalogo FIDE oppure inserirti manualmente. Se ti inserisci manualmente partirai con rating 1399."}
          </CardDescription>
        </CardHeader>
        <CardContent className="overflow-y-auto">
          {tournamentDetail?.type === "team" ? (
            <TeamTournamentRegistrationContent onClose={onClose} tournament={tournamentDetail} />
          ) : (
            <IndividualTournamentRegistrationContent onClose={onClose} tournament={tournament} />
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function IndividualTournamentRegistrationContent({ onClose, tournament }: Props) {
  const [mode, setMode] = useState<"fide" | "manual">("fide");
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);
  const [selectedFideId, setSelectedFideId] = useState<string | null>(null);
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [feedback, setFeedback] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const registrationMutation = usePublicTournamentRegistration(String(tournament.id));
  const { data: fidePlayers, isFetching } = useFideSearch(query, tournament.time_control_category);

  const registrationClosed = tournament.is_registration_closed;
  const canSubmitManual = firstName.trim().length >= 2 && lastName.trim().length >= 2 && !registrationClosed;
  const visibleResults = useMemo(() => fidePlayers ?? [], [fidePlayers]);
  const pageSize = 5;
  const totalPages = Math.max(1, Math.ceil(visibleResults.length / pageSize));
  const safePage = Math.min(page, totalPages);
  const paginatedResults = visibleResults.slice((safePage - 1) * pageSize, safePage * pageSize);
  const selectedFidePlayer = visibleResults.find((player) => player.fide_id === selectedFideId) ?? null;

  useEffect(() => {
    setPage(1);
    setSelectedFideId(null);
  }, [query, mode]);

  async function handleSubmit() {
    setFeedback(null);
    try {
      if (mode === "fide") {
        if (!selectedFidePlayer || registrationClosed) return;
        await registrationMutation.mutateAsync({ fide_id: selectedFidePlayer.fide_id });
      } else {
        await registrationMutation.mutateAsync({ first_name: firstName, last_name: lastName });
      }
      setSuccessMessage("Iscrizione completata con successo.");
    } catch (error) {
      setFeedback(readErrorMessage(error));
    }
  }

  if (successMessage) {
    return <SuccessPanel message={successMessage} onClose={onClose} />;
  }

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap gap-2">
        <Button onClick={() => setMode("fide")} variant={mode === "fide" ? "default" : "outline"}>
          Ricerca FIDE
        </Button>
        <Button onClick={() => setMode("manual")} variant={mode === "manual" ? "default" : "outline"}>
          Inserimento manuale
        </Button>
      </div>

      {registrationClosed ? <div className="text-sm text-red-400">Le iscrizioni di questo torneo sono chiuse.</div> : null}

      {mode === "fide" ? (
        <FideSelectionPanel
          emptyLabel={isFetching ? "Ricerca in corso..." : "Nessun profilo trovato."}
          page={safePage}
          paginatedResults={paginatedResults}
          query={query}
          selectedFideId={selectedFideId}
          setPage={setPage}
          setQuery={setQuery}
          setSelectedFideId={setSelectedFideId}
          totalPages={totalPages}
          totalResults={visibleResults.length}
        />
      ) : (
        <ManualIdentityPanel firstName={firstName} lastName={lastName} setFirstName={setFirstName} setLastName={setLastName} />
      )}

      <FooterActions
        feedback={feedback}
        onClose={onClose}
        onSubmit={() => void handleSubmit()}
        submitDisabled={
          mode === "fide"
            ? !selectedFidePlayer || registrationClosed || registrationMutation.isPending
            : !canSubmitManual || registrationMutation.isPending
        }
        submitLabel="Iscriviti"
      />
    </div>
  );
}

function TeamTournamentRegistrationContent({ onClose, tournament }: { onClose: () => void; tournament: TournamentDetail }) {
  const [mode, setMode] = useState<"create" | "join" | "solo">("create");
  const [createIdentityMode, setCreateIdentityMode] = useState<"fide" | "manual">("fide");
  const [joinIdentityMode, setJoinIdentityMode] = useState<"fide" | "manual">("fide");
  const [createQuery, setCreateQuery] = useState("");
  const [joinQuery, setJoinQuery] = useState("");
  const [createPage, setCreatePage] = useState(1);
  const [joinPage, setJoinPage] = useState(1);
  const [selectedCreateFideId, setSelectedCreateFideId] = useState<string | null>(null);
  const [selectedJoinFideId, setSelectedJoinFideId] = useState<string | null>(null);
  const [createFirstName, setCreateFirstName] = useState("");
  const [createLastName, setCreateLastName] = useState("");
  const [joinFirstName, setJoinFirstName] = useState("");
  const [joinLastName, setJoinLastName] = useState("");
  const [teamName, setTeamName] = useState("");
  const [selectedTeamId, setSelectedTeamId] = useState<number | null>(tournament.teams[0]?.id ?? null);
  const [teamPin, setTeamPin] = useState("");
  const [feedback, setFeedback] = useState<string | null>(null);
  const [createdTeam, setCreatedTeam] = useState<PublicTeamRegistrationCreateResponse | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [captainMemberId, setCaptainMemberId] = useState<string | null>(null);
  const [teammates, setTeammates] = useState<DraftTeammate[]>([]);

  const createMutation = useCreatePublicTeamRegistration(String(tournament.id));
  const joinMutation = useJoinPublicTeamRegistration(String(tournament.id));
  const soloMutation = usePublicTournamentRegistration(String(tournament.id));
  const { data: createFidePlayers = [], isFetching: isFetchingCreateFide } = useFideSearch(createQuery, tournament.time_control_category);
  const { data: joinFidePlayers = [], isFetching: isFetchingJoinFide } = useFideSearch(joinQuery, tournament.time_control_category);

  const availableCreateFidePlayers = createFidePlayers.filter((player) => !tournament.players.some((entry) => entry.fide_id === player.fide_id));
  const createSelection = availableCreateFidePlayers.find((player) => player.fide_id === selectedCreateFideId) ?? null;
  const joinSelection = joinFidePlayers.find((player) => player.fide_id === selectedJoinFideId) ?? null;

  const pageSize = 5;
  const createTotalPages = Math.max(1, Math.ceil(availableCreateFidePlayers.length / pageSize));
  const joinTotalPages = Math.max(1, Math.ceil(joinFidePlayers.length / pageSize));
  const safeCreatePage = Math.min(createPage, createTotalPages);
  const safeJoinPage = Math.min(joinPage, joinTotalPages);
  const paginatedCreateFidePlayers = availableCreateFidePlayers.slice((safeCreatePage - 1) * pageSize, safeCreatePage * pageSize);
  const paginatedJoinFidePlayers = joinFidePlayers.slice((safeJoinPage - 1) * pageSize, safeJoinPage * pageSize);

  const registrationClosed = tournament.is_registration_closed;
  const canSubmitCreate =
    !registrationClosed && teamName.trim().length >= 2 && teammates.length > 0 && !!captainMemberId && !createMutation.isPending;
  const canSubmitJoin =
    !registrationClosed &&
    !!selectedTeamId &&
    teamPin.trim().length === 4 &&
    hasValidIdentity(joinIdentityMode, joinSelection, joinFirstName, joinLastName) &&
    !joinMutation.isPending;
  const canSubmitSolo =
    !registrationClosed && hasValidIdentity(joinIdentityMode, joinSelection, joinFirstName, joinLastName) && !soloMutation.isPending;

  useEffect(() => {
    setFeedback(null);
  }, [mode]);

  useEffect(() => {
    setCreatePage(1);
    setSelectedCreateFideId(null);
  }, [createQuery, createIdentityMode]);

  useEffect(() => {
    setJoinPage(1);
    setSelectedJoinFideId(null);
  }, [joinQuery, joinIdentityMode]);

  function addCreateMember() {
    const payload = buildRegistrationPayload(createIdentityMode, createSelection, createFirstName, createLastName);
    if (!payload) return;

    const draft = buildDraftTeammate(payload, readIdentityLabel(createIdentityMode, createSelection, createFirstName, createLastName));
    setTeammates((current) => {
      if (current.some((entry) => entry.id === draft.id)) return current;
      return [...current, draft];
    });
    setCaptainMemberId((current) => current ?? draft.id);
    setCreateQuery("");
    setSelectedCreateFideId(null);
    setCreateFirstName("");
    setCreateLastName("");
  }

  function removeTeammate(id: string) {
    setTeammates((current) => current.filter((entry) => entry.id !== id));
    setCaptainMemberId((current) => (current === id ? null : current));
  }

  function moveTeammate(id: string, direction: -1 | 1) {
    setTeammates((current) => {
      const index = current.findIndex((entry) => entry.id === id);
      const nextIndex = index + direction;
      if (index < 0 || nextIndex < 0 || nextIndex >= current.length) return current;
      const clone = [...current];
      [clone[index], clone[nextIndex]] = [clone[nextIndex], clone[index]];
      return clone;
    });
  }

  async function handleCreateTeam() {
    const captain = teammates.find((entry) => entry.id === captainMemberId);
    if (!captain) return;
    setFeedback(null);
    try {
      const response = await createMutation.mutateAsync({
        team_name: teamName.trim(),
        captain: teammateToPayload(captain),
        teammate_player_ids: teammates.filter((entry) => entry.id !== captain.id && entry.kind === "existing").map((entry) => entry.playerId ?? 0),
        teammate_fide_ids: teammates.filter((entry) => entry.id !== captain.id && entry.kind === "fide").map((entry) => entry.fideId ?? ""),
        teammate_manual_entries: teammates
          .filter((entry) => entry.id !== captain.id && entry.kind === "manual")
          .map((entry) => ({ first_name: entry.firstName, last_name: entry.lastName })),
      });
      setCreatedTeam(response);
      setTeammates([]);
      setCaptainMemberId(null);
    } catch (error) {
      setFeedback(readErrorMessage(error));
    }
  }

  async function handleJoinTeam() {
    setFeedback(null);
    try {
      const registrant = buildRegistrationPayload(joinIdentityMode, joinSelection, joinFirstName, joinLastName);
      if (!registrant) return;
      await joinMutation.mutateAsync({ team_id: selectedTeamId ?? 0, pin: teamPin.trim(), registrant });
      setSuccessMessage("Iscrizione alla squadra completata con successo.");
    } catch (error) {
      setFeedback(readErrorMessage(error));
    }
  }

  async function handleSoloRegistration() {
    setFeedback(null);
    try {
      const registrant = buildRegistrationPayload(joinIdentityMode, joinSelection, joinFirstName, joinLastName);
      if (!registrant) return;
      await soloMutation.mutateAsync(registrant);
      setSuccessMessage("Iscrizione completata con successo.");
    } catch (error) {
      setFeedback(readErrorMessage(error));
    }
  }

  if (successMessage) {
    return <SuccessPanel message={successMessage} onClose={onClose} />;
  }

  if (createdTeam) {
    return (
      <div className="space-y-5">
        <Card className="border-emerald-200 bg-emerald-50">
          <CardHeader>
            <CardTitle>Squadra creata</CardTitle>
            <CardDescription>Condividi questo PIN con chi vuole unirsi alla tua squadra.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-2xl border bg-white p-4">
              <div className="text-sm text-[var(--muted-foreground)]">Squadra</div>
              <div className="mt-1 text-lg font-semibold">{createdTeam.team_name}</div>
            </div>
            <div className="rounded-2xl border bg-white p-4 text-center">
              <div className="text-sm text-[var(--muted-foreground)]">PIN di accesso</div>
              <div className="mt-2 text-4xl font-bold tracking-[0.4em]">{createdTeam.pin}</div>
            </div>
            <div className="text-sm text-[var(--muted-foreground)]">Giocatori registrati nella squadra: {createdTeam.members_count}</div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setCreatedTeam(null)}>
                Crea un'altra squadra
              </Button>
              <Button onClick={onClose}>Chiudi</Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap gap-2">
        <Button onClick={() => setMode("create")} variant={mode === "create" ? "default" : "outline"}>
          Crea squadra
        </Button>
        <Button onClick={() => setMode("join")} variant={mode === "join" ? "default" : "outline"}>
          Unisciti a squadra
        </Button>
        <Button onClick={() => setMode("solo")} variant={mode === "solo" ? "default" : "outline"}>
          Senza squadra
        </Button>
      </div>

      {registrationClosed ? <div className="text-sm text-red-400">Le iscrizioni di questo torneo sono chiuse.</div> : null}

      {mode === "create" ? (
        <div className="space-y-5">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Squadra</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <Label htmlFor="team-name">Nome squadra</Label>
                <Input id="team-name" value={teamName} onChange={(event) => setTeamName(event.target.value)} />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Aggiungi membro</CardTitle>
              <CardDescription>Aggiungi qui i giocatori che faranno parte della squadra, incluso te stesso.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-wrap gap-2">
                <Button onClick={() => setCreateIdentityMode("fide")} variant={createIdentityMode === "fide" ? "default" : "outline"}>
                  Ricerca FIDE
                </Button>
                <Button onClick={() => setCreateIdentityMode("manual")} variant={createIdentityMode === "manual" ? "default" : "outline"}>
                  Inserimento manuale
                </Button>
              </div>
              {createIdentityMode === "fide" ? (
                <FideSelectionPanel
                  emptyLabel={isFetchingCreateFide ? "Ricerca in corso..." : "Nessun profilo trovato."}
                  page={safeCreatePage}
                  paginatedResults={paginatedCreateFidePlayers}
                  query={createQuery}
                  selectedFideId={selectedCreateFideId}
                  setPage={setCreatePage}
                  setQuery={setCreateQuery}
                  setSelectedFideId={setSelectedCreateFideId}
                  totalPages={createTotalPages}
                  totalResults={availableCreateFidePlayers.length}
                />
              ) : (
                <ManualIdentityPanel
                  firstName={createFirstName}
                  lastName={createLastName}
                  setFirstName={setCreateFirstName}
                  setLastName={setCreateLastName}
                />
              )}
              <div className="flex justify-end">
                <Button disabled={!hasValidIdentity(createIdentityMode, createSelection, createFirstName, createLastName)} onClick={addCreateMember}>
                  <UserPlus className="h-4 w-4" />
                  Aggiungi membro
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Composizione squadra</CardTitle>
              <CardDescription>Seleziona il capitano, cambia l'ordine e rimuovi membri.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-5">
              <div className="space-y-2">
                {teammates.map((teammate, index) => (
                  <RosterRow
                    key={teammate.id}
                    isCaptain={captainMemberId === teammate.id}
                    label={teammate.label}
                    onMoveDown={index < teammates.length - 1 ? () => moveTeammate(teammate.id, 1) : undefined}
                    onMoveUp={index > 0 ? () => moveTeammate(teammate.id, -1) : undefined}
                    onRemove={() => removeTeammate(teammate.id)}
                    onSetCaptain={() => setCaptainMemberId(teammate.id)}
                  />
                ))}
                {!teammates.length ? <div className="text-sm text-[var(--muted-foreground)]">Nessun membro aggiunto alla squadra.</div> : null}
              </div>
            </CardContent>
          </Card>

          <FooterActions
            feedback={feedback}
            onClose={onClose}
            onSubmit={() => void handleCreateTeam()}
            submitDisabled={!canSubmitCreate}
            submitLabel={createMutation.isPending ? "Creazione..." : "Crea squadra"}
          />
        </div>
      ) : mode === "join" ? (
        <div className="space-y-6">
          <div className="grid gap-4 md:grid-cols-[minmax(0,1fr)_160px]">
            <div className="space-y-2">
              <Label htmlFor="join-team">Squadra</Label>
              <select
                id="join-team"
                className="h-10 w-full rounded-xl border bg-white px-3 text-sm"
                value={selectedTeamId ?? ""}
                onChange={(event) => setSelectedTeamId(event.target.value ? Number(event.target.value) : null)}
              >
                <option value="">Seleziona squadra</option>
                {tournament.teams.map((team) => (
                  <option key={team.id} value={team.id}>
                    {team.name} ({team.members_count} giocatori)
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="join-pin">PIN</Label>
              <Input
                id="join-pin"
                inputMode="numeric"
                maxLength={4}
                value={teamPin}
                onChange={(event) => setTeamPin(event.target.value.replace(/\D/g, "").slice(0, 4))}
              />
            </div>
          </div>

          <IdentityCard
            firstName={joinFirstName}
            identityMode={joinIdentityMode}
            isFetching={isFetchingJoinFide}
            lastName={joinLastName}
            onIdentityModeChange={setJoinIdentityMode}
            onQueryChange={setJoinQuery}
            page={safeJoinPage}
            query={joinQuery}
            results={paginatedJoinFidePlayers}
            selectedFideId={selectedJoinFideId}
            setFirstName={setJoinFirstName}
            setLastName={setJoinLastName}
            setPage={setJoinPage}
            setSelectedFideId={setSelectedJoinFideId}
            title="Giocatore"
            totalPages={joinTotalPages}
            totalResults={joinFidePlayers.length}
          />

          <FooterActions
            feedback={feedback}
            onClose={onClose}
            onSubmit={() => void handleJoinTeam()}
            submitDisabled={!canSubmitJoin}
            submitLabel={joinMutation.isPending ? "Iscrizione..." : "Unisciti alla squadra"}
          />
        </div>
      ) : (
        <div className="space-y-6">
          <IdentityCard
            firstName={joinFirstName}
            identityMode={joinIdentityMode}
            isFetching={isFetchingJoinFide}
            lastName={joinLastName}
            onIdentityModeChange={setJoinIdentityMode}
            onQueryChange={setJoinQuery}
            page={safeJoinPage}
            query={joinQuery}
            results={paginatedJoinFidePlayers}
            selectedFideId={selectedJoinFideId}
            setFirstName={setJoinFirstName}
            setLastName={setJoinLastName}
            setPage={setJoinPage}
            setSelectedFideId={setSelectedJoinFideId}
            title="Iscrizione senza squadra"
            description="Puoi iscriverti anche senza squadra e resterai nel pool dei giocatori senza squadra."
            totalPages={joinTotalPages}
            totalResults={joinFidePlayers.length}
          />

          <FooterActions
            feedback={feedback}
            onClose={onClose}
            onSubmit={() => void handleSoloRegistration()}
            submitDisabled={!canSubmitSolo}
            submitLabel={soloMutation.isPending ? "Iscrizione..." : "Iscriviti senza squadra"}
          />
        </div>
      )}
    </div>
  );
}

function IdentityCard({
  description,
  firstName,
  identityMode,
  isFetching,
  lastName,
  onIdentityModeChange,
  onQueryChange,
  page,
  query,
  results,
  selectedFideId,
  setFirstName,
  setLastName,
  setPage,
  setSelectedFideId,
  title,
  totalPages,
  totalResults,
}: {
  description?: string;
  firstName: string;
  identityMode: "fide" | "manual";
  isFetching: boolean;
  lastName: string;
  onIdentityModeChange: (value: "fide" | "manual") => void;
  onQueryChange: (value: string) => void;
  page: number;
  query: string;
  results: FidePlayer[];
  selectedFideId: string | null;
  setFirstName: (value: string) => void;
  setLastName: (value: string) => void;
  setPage: (value: number | ((current: number) => number)) => void;
  setSelectedFideId: (value: string | null) => void;
  title: string;
  totalPages: number;
  totalResults: number;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">{title}</CardTitle>
        {description ? <CardDescription>{description}</CardDescription> : null}
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap gap-2">
          <Button onClick={() => onIdentityModeChange("fide")} variant={identityMode === "fide" ? "default" : "outline"}>
            Ricerca FIDE
          </Button>
          <Button onClick={() => onIdentityModeChange("manual")} variant={identityMode === "manual" ? "default" : "outline"}>
            Inserimento manuale
          </Button>
        </div>
        {identityMode === "fide" ? (
          <FideSelectionPanel
            emptyLabel={isFetching ? "Ricerca in corso..." : "Nessun profilo trovato."}
            page={page}
            paginatedResults={results}
            query={query}
            selectedFideId={selectedFideId}
            setPage={setPage}
            setQuery={onQueryChange}
            setSelectedFideId={setSelectedFideId}
            totalPages={totalPages}
            totalResults={totalResults}
          />
        ) : (
          <ManualIdentityPanel firstName={firstName} lastName={lastName} setFirstName={setFirstName} setLastName={setLastName} />
        )}
      </CardContent>
    </Card>
  );
}

function RosterRow({
  isCaptain = false,
  label,
  onMoveDown,
  onMoveUp,
  onRemove,
  onSetCaptain,
}: {
  isCaptain?: boolean;
  label: string;
  onMoveDown?: () => void;
  onMoveUp?: () => void;
  onRemove?: () => void;
  onSetCaptain?: () => void;
}) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-xl border bg-white px-3 py-2 text-sm">
      <div className="flex items-center gap-2">
        {isCaptain ? <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium">Capitano</span> : null}
        <span>{label}</span>
      </div>
      <div className="flex gap-2">
        {onSetCaptain && !isCaptain ? (
          <Button onClick={onSetCaptain} size="sm" type="button" variant="outline">
            Capitano
          </Button>
        ) : null}
        {onMoveUp ? (
          <Button onClick={onMoveUp} size="sm" type="button" variant="outline">
            <ArrowUp className="h-4 w-4" />
          </Button>
        ) : null}
        {onMoveDown ? (
          <Button onClick={onMoveDown} size="sm" type="button" variant="outline">
            <ArrowDown className="h-4 w-4" />
          </Button>
        ) : null}
        {onRemove ? (
          <Button onClick={onRemove} size="sm" type="button" variant="outline">
            <Trash2 className="h-4 w-4" />
          </Button>
        ) : null}
      </div>
    </div>
  );
}

function ManualIdentityPanel({
  firstName,
  lastName,
  setFirstName,
  setLastName,
}: {
  firstName: string;
  lastName: string;
  setFirstName: (value: string) => void;
  setLastName: (value: string) => void;
}) {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <div className="space-y-2">
        <Label htmlFor="registration-last-name">Cognome</Label>
        <Input id="registration-last-name" value={lastName} onChange={(event) => setLastName(event.target.value)} />
      </div>
      <div className="space-y-2">
        <Label htmlFor="registration-first-name">Nome</Label>
        <Input id="registration-first-name" value={firstName} onChange={(event) => setFirstName(event.target.value)} />
      </div>
    </div>
  );
}

function FideSelectionPanel({
  emptyLabel,
  page,
  paginatedResults,
  query,
  selectedFideId,
  setPage,
  setQuery,
  setSelectedFideId,
  totalPages,
  totalResults,
}: {
  emptyLabel: string;
  page: number;
  paginatedResults: FidePlayer[];
  query: string;
  selectedFideId: string | null;
  setPage: (value: number | ((current: number) => number)) => void;
  setQuery: (value: string) => void;
  setSelectedFideId: (value: string | null) => void;
  totalPages: number;
  totalResults: number;
}) {
  return (
    <div className="space-y-4">
      <div className="relative max-w-xl">
        <Search className="pointer-events-none absolute left-3 top-3.5 h-4 w-4 text-[var(--muted-foreground)]" />
        <Input className="pl-9" placeholder="Cerca nome FIDE" value={query} onChange={(event) => setQuery(event.target.value)} />
      </div>
      {query.trim().length >= 2 ? (
        <SingleSelectFideTable
          emptyLabel={emptyLabel}
          page={page}
          players={paginatedResults}
          selectedFideId={selectedFideId}
          setPage={setPage}
          setSelectedFideId={setSelectedFideId}
          totalPages={totalPages}
          totalResults={totalResults}
        />
      ) : null}
    </div>
  );
}

function SingleSelectFideTable({
  emptyLabel,
  page,
  players,
  selectedFideId,
  setPage,
  setSelectedFideId,
  totalPages,
  totalResults,
}: {
  emptyLabel: string;
  page: number;
  players: FidePlayer[];
  selectedFideId: string | null;
  setPage: (value: number | ((current: number) => number)) => void;
  setSelectedFideId: (value: string | null) => void;
  totalPages: number;
  totalResults: number;
}) {
  return (
    <div className="space-y-3 overflow-x-auto">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Nome</TableHead>
            <TableHead>FIDE ID</TableHead>
            <TableHead>FED</TableHead>
            <TableHead>Std</TableHead>
            <TableHead>Rapid</TableHead>
            <TableHead>Blitz</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {players.map((player) => (
            <TableRow
              className={selectedFideId === player.fide_id ? "cursor-pointer bg-slate-200/80" : "cursor-pointer"}
              key={player.fide_id}
              onClick={() => setSelectedFideId(player.fide_id)}
            >
              <TableCell className="min-w-56">{player.full_name}</TableCell>
              <TableCell>{player.fide_id}</TableCell>
              <TableCell>
                <FederationCell federation={player.federation} />
              </TableCell>
              <TableCell>{player.standard_rating ?? player.rating ?? "-"}</TableCell>
              <TableCell>{player.rapid_rating ?? "-"}</TableCell>
              <TableCell>{player.blitz_rating ?? "-"}</TableCell>
            </TableRow>
          ))}
          {!players.length ? (
            <TableRow>
              <TableCell className="text-[var(--muted-foreground)]" colSpan={6}>
                {emptyLabel}
              </TableCell>
            </TableRow>
          ) : null}
        </TableBody>
      </Table>
      <PaginationControls page={page} setPage={setPage} totalPages={totalPages} totalResults={totalResults} />
    </div>
  );
}

function PaginationControls({
  page,
  setPage,
  totalPages,
  totalResults,
}: {
  page: number;
  setPage: (value: number | ((current: number) => number)) => void;
  totalPages: number;
  totalResults: number;
}) {
  if (totalResults <= 5) return null;

  return (
    <div className="flex items-center justify-between gap-3 text-sm">
      <div className="text-[var(--muted-foreground)]">
        Pagina {page} di {totalPages}
      </div>
      <div className="flex gap-2">
        <Button disabled={page <= 1} onClick={() => setPage((current) => Math.max(1, current - 1))} size="sm" variant="outline">
          Prec.
        </Button>
        <Button disabled={page >= totalPages} onClick={() => setPage((current) => Math.min(totalPages, current + 1))} size="sm" variant="outline">
          Succ.
        </Button>
      </div>
    </div>
  );
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

function FooterActions({
  feedback,
  onClose,
  onSubmit,
  submitDisabled,
  submitLabel,
}: {
  feedback: string | null;
  onClose: () => void;
  onSubmit: () => void;
  submitDisabled: boolean;
  submitLabel: string;
}) {
  return (
    <div className="flex items-center justify-between gap-3">
      <div className="text-sm text-red-600">{feedback}</div>
      <div className="flex items-center gap-2">
        <Button disabled={submitDisabled} onClick={onSubmit}>
          {submitLabel}
        </Button>
        <Button onClick={onClose} variant="outline">
          Chiudi
        </Button>
      </div>
    </div>
  );
}

function SuccessPanel({ message, onClose }: { message: string; onClose: () => void }) {
  return (
    <Card className="border-emerald-200 bg-emerald-50">
      <CardHeader>
        <CardTitle>Operazione completata</CardTitle>
        <CardDescription>{message}</CardDescription>
      </CardHeader>
      <CardContent className="flex justify-end">
        <Button onClick={onClose}>Chiudi</Button>
      </CardContent>
    </Card>
  );
}

function hasValidIdentity(mode: "fide" | "manual", selectedFidePlayer: FidePlayer | null, firstName: string, lastName: string) {
  return mode === "fide" ? !!selectedFidePlayer : firstName.trim().length >= 2 && lastName.trim().length >= 2;
}

function readIdentityLabel(mode: "fide" | "manual", selectedFidePlayer: FidePlayer | null, firstName: string, lastName: string) {
  if (mode === "fide" && selectedFidePlayer) {
    return selectedFidePlayer.full_name;
  }
  return `${lastName.trim()}, ${firstName.trim()}`;
}

function buildRegistrationPayload(
  mode: "fide" | "manual",
  selectedFidePlayer: FidePlayer | null,
  firstName: string,
  lastName: string,
): TournamentPublicRegistration | null {
  if (mode === "fide") {
    return selectedFidePlayer ? { fide_id: selectedFidePlayer.fide_id } : null;
  }
  if (firstName.trim().length < 2 || lastName.trim().length < 2) {
    return null;
  }
  return { first_name: firstName.trim(), last_name: lastName.trim() };
}

function buildDraftTeammate(payload: TournamentPublicRegistration, label: string, existingPlayerId?: number): DraftTeammate {
  if (existingPlayerId) {
    return { id: `existing-${existingPlayerId}`, label, kind: "existing", playerId: existingPlayerId };
  }
  if (payload.fide_id) {
    return { id: `fide-${payload.fide_id}`, label, kind: "fide", fideId: payload.fide_id };
  }
  return {
    id: `manual-${payload.last_name?.toLowerCase()}-${payload.first_name?.toLowerCase()}`,
    label,
    kind: "manual",
    firstName: payload.first_name,
    lastName: payload.last_name,
  };
}

function teammateToPayload(teammate: DraftTeammate): TournamentPublicRegistration {
  if (teammate.kind === "fide") return { fide_id: teammate.fideId };
  if (teammate.kind === "manual") return { first_name: teammate.firstName, last_name: teammate.lastName };
  return { first_name: teammate.label.split(", ")[1] ?? "", last_name: teammate.label.split(", ")[0] ?? "" };
}

function readErrorMessage(error: unknown) {
  if (isAxiosError(error)) {
    const message = error.response?.data?.message;
    if (typeof message === "string") return message;
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail) && detail.length > 0) {
      const firstIssue = detail[0];
      if (typeof firstIssue?.msg === "string") return firstIssue.msg.replace(/^Value error,\s*/i, "");
    }
    return error.message || "Non sono riuscito a completare l'iscrizione.";
  }
  if (error instanceof Error) return error.message;
  return "Non sono riuscito a completare l'iscrizione.";
}
