import { useMemo, useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { ArrowRight, Plus, Search, SquarePen, Trash2 } from "lucide-react";
import { api } from "@/api/client";
import { useTournaments } from "@/api/hooks/tournaments";
import { useAuth } from "@/auth/useAuth";
import { AppShell } from "@/components/layout/AppShell";
import { TournamentHeroCard } from "@/components/tournaments/TournamentHeroCard";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { TournamentRegistrationDialog } from "@/components/tournaments/TournamentRegistrationDialog";

export function TournamentsPage() {
  const { isAuthenticated, user } = useAuth();
  const { data: tournaments, isLoading } = useTournaments();
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [registrationTournamentId, setRegistrationTournamentId] = useState<number | null>(null);
  const filteredTournaments = useMemo(() => filterTournamentsByName(tournaments ?? [], query), [query, tournaments]);
  const groupedTournaments = groupTournamentsByMonth(filteredTournaments);
  const registrationTournament = filteredTournaments.find((tournament) => tournament.id === registrationTournamentId) ?? null;

  if (isAuthenticated && user?.must_change_password) {
    return <Navigate replace to="/change-password" />;
  }

  return (
    <AppShell>
      {registrationTournament ? (
        <TournamentRegistrationDialog onClose={() => setRegistrationTournamentId(null)} tournament={registrationTournament} />
      ) : null}
      <section className="mb-8">
        <h1 className="text-3xl font-semibold">Tornei</h1>
      </section>

      <section className="mb-8">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="relative max-w-xl flex-1">
            <Search className="pointer-events-none absolute left-3 top-3.5 h-4 w-4 text-[var(--muted-foreground)]" />
            <Input className="pl-9" placeholder="Cerca tornei per nome" value={query} onChange={(event) => setQuery(event.target.value)} />
          </div>
          {isAuthenticated ? (
            <Button asChild className="shrink-0">
              <Link to="/tournaments/new">
                <Plus className="h-4 w-4" />
                Crea torneo
              </Link>
            </Button>
          ) : null}
        </div>
      </section>

      <section className="space-y-4">
        {groupedTournaments.map((group, index) => (
          <div key={group.key} className="space-y-4">
            <MonthDivider label={group.label} year={group.year} showYear={index === 0 || groupedTournaments[index - 1].year !== group.year} />
            {group.tournaments.map((tournament) => (
              <div key={tournament.id} className="cursor-pointer" onClick={() => navigate(`/tournaments/${tournament.id}`)}>
                <TournamentHeroCard
                  bulletinUrl={tournament.bulletin_url}
                  datesLabel={formatTournamentDates(tournament.start_date, tournament.end_date)}
                  description={tournament.description}
                  isEloRated={tournament.is_elo_rated}
                  isOwner={user?.id === tournament.owner_id}
                  isPrivate={tournament.is_private}
                  name={tournament.name}
                  onRegister={
                    !tournament.is_private && !tournament.is_registration_closed ? () => setRegistrationTournamentId(tournament.id) : undefined
                  }
                  participantsLabel={`${tournament.type === "team" ? tournament.teams_count : tournament.players_count}`}
                  registerButtonLabel="Iscriviti"
                  roundsLabel={`${tournament.rounds_count} turni`}
                  secondaryActions={
                    tournament.can_manage ? (
                      <>
                        <Button
                          asChild
                          className="border bg-white text-slate-500 shadow-sm hover:bg-slate-50"
                          onClick={(event) => event.stopPropagation()}
                          variant="outline"
                          aria-label="Modifica torneo"
                          title="Modifica torneo"
                        >
                          <Link to={`/tournaments/${tournament.id}/edit`}>
                            <SquarePen className="h-4 w-4" />
                          </Link>
                        </Button>
                        <Button
                          onClick={(event) => {
                            event.stopPropagation();
                            void api.deleteTournament(String(tournament.id)).then(() => navigate(0));
                          }}
                          variant="outline"
                          className="border bg-white text-slate-500 shadow-sm hover:bg-slate-50"
                          aria-label="Elimina torneo"
                          title="Elimina torneo"
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
              </div>
            ))}
          </div>
        ))}
        {!isLoading && !filteredTournaments.length ? (
          <Card>
            <CardContent className="flex items-center justify-between pt-6">
              <div>
                <CardTitle>{query.trim() ? "Nessun torneo trovato" : "Nessun torneo configurato"}</CardTitle>
                <CardDescription>
                  {query.trim()
                    ? "Prova a cercare con un'altra parola del nome del torneo."
                    : isAuthenticated
                      ? "Crea il primo torneo per iniziare la gestione pairings."
                      : "Non ci sono ancora tornei pubblicati."}
                </CardDescription>
              </div>
              {isAuthenticated ? (
                <Button asChild>
                  <Link to="/tournaments/new">
                    Inizia <ArrowRight className="h-4 w-4" />
                  </Link>
                </Button>
              ) : null}
            </CardContent>
          </Card>
        ) : null}
      </section>
    </AppShell>
  );
}

function MonthDivider({ label, year, showYear }: { label: string; year: number; showYear: boolean }) {
  return (
    <div className="space-y-2 py-2">
      {showYear ? <div className="text-2xl font-semibold text-[var(--foreground)]">{year}</div> : null}
      <div className="flex items-center gap-4">
        <div className="h-px flex-1 bg-[var(--border)]" />
        <div className="text-sm font-semibold uppercase tracking-[0.2em] text-[var(--muted-foreground)]">{label}</div>
        <div className="h-px flex-1 bg-[var(--border)]" />
      </div>
    </div>
  );
}

function formatTournamentDates(startDate: string, endDate: string) {
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

function groupTournamentsByMonth<T extends { start_date: string } & { id: number }>(tournaments: T[]) {
  const sortedTournaments = [...tournaments].sort((left, right) => left.start_date.localeCompare(right.start_date));
  const groups: Array<{ key: string; label: string; year: number; tournaments: T[] }> = [];

  sortedTournaments.forEach((tournament) => {
    const date = new Date(`${tournament.start_date}T00:00:00`);
    const key = `${date.getFullYear()}-${date.getMonth()}`;
    const label = new Intl.DateTimeFormat("it-IT", { month: "long" }).format(date);
    const year = date.getFullYear();
    const currentGroup = groups[groups.length - 1];

    if (currentGroup?.key === key) {
      currentGroup.tournaments.push(tournament);
      return;
    }

    groups.push({ key, label, year, tournaments: [tournament] });
  });

  return groups;
}

function filterTournamentsByName<T extends { name: string }>(tournaments: T[], query: string) {
  const normalizedQuery = normalizeSearch(query);
  if (!normalizedQuery) {
    return tournaments;
  }

  const queryTerms = normalizedQuery.split(" ").filter(Boolean);
  return tournaments.filter((tournament) => {
    const normalizedName = normalizeSearch(tournament.name);
    return queryTerms.every((term) => normalizedName.includes(term));
  });
}

function normalizeSearch(value: string) {
  return value
    .toLocaleLowerCase()
    .normalize("NFD")
    .replace(/[^\p{L}\p{N}\s]/gu, " ")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/\s+/g, " ")
    .trim();
}
