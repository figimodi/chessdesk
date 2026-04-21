import { useMemo, useState, type ReactNode } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { ArrowRight, CalendarDays, ChartColumn, Clock3, Hash, LockKeyhole, MapPin, Paperclip, Plus, Search, User, Users, Zap, Turtle } from "lucide-react";
import { useTournaments } from "@/api/hooks/tournaments";
import { useAuth } from "@/auth/AuthContext";
import { AppShell } from "@/components/layout/AppShell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { TournamentRegistrationDialog } from "@/components/tournaments/TournamentRegistrationDialog";

export function TournamentsPage() {
  const { isAuthenticated, user } = useAuth();
  const { data: tournaments, isLoading } = useTournaments();
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [registrationTournamentId, setRegistrationTournamentId] = useState<number | null>(null);
  const filteredTournaments = useMemo(
    () => filterTournamentsByName(tournaments ?? [], query),
    [query, tournaments],
  );
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
      <section className="mb-8 flex items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold">Tornei</h1>
          <p className="text-sm text-[var(--muted-foreground)]">
            {isAuthenticated
              ? user?.role === "admin"
                ? "Controlla tutti i tornei della piattaforma e gestisci gli account."
                : "Consulta tutti i tornei pubblici e gestisci solo quelli di cui sei proprietario."
              : "Consulta tutti i tornei pubblici. Accedi dalla home per crearne o gestirne uno."}
          </p>
        </div>
        {isAuthenticated ? (
          <Button asChild>
            <Link to="/tournaments/new">
              <Plus className="h-4 w-4" />
              Crea torneo
            </Link>
          </Button>
        ) : null}
      </section>

      <section className="mb-8">
        <div className="relative max-w-xl">
          <Search className="pointer-events-none absolute left-3 top-3.5 h-4 w-4 text-[var(--muted-foreground)]" />
          <Input
            className="pl-9"
            placeholder="Cerca tornei per nome"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
        </div>
      </section>

      <section className="space-y-4">
        {groupedTournaments.map((group, index) => (
          <div key={group.key} className="space-y-4">
            <MonthDivider label={group.label} year={group.year} showYear={index === 0 || groupedTournaments[index - 1].year !== group.year} />
            {group.tournaments.map((tournament) => (
              <Card key={tournament.id} className="cursor-pointer" onClick={() => navigate(`/tournaments/${tournament.id}`)}>
                <CardHeader>
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <CardTitle>{tournament.name}</CardTitle>
                    </div>
                    <Badge>{tournament.type === "team" ? "Squadre" : "Individuale"}</Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid gap-3 md:grid-cols-2">
                    <DetailHighlightCard icon={<MapPin className="h-4 w-4" />} label="Luogo" value={tournament.venue ?? "Sede da definire"} />
                    <DetailHighlightCard
                      icon={<CalendarDays className="h-4 w-4" />}
                      label="Date"
                      value={formatTournamentDates(tournament.start_date, tournament.end_date)}
                    />
                  </div>
                  <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
                    <div className="flex flex-wrap gap-2">
                      <InfoChip icon={<ChartColumn className="h-4 w-4" />} label={tournament.is_elo_rated ? "Variazione Elo" : "No variazione Elo"} />
                      {tournament.bulletin_url ? (
                        <InfoChip icon={<Paperclip className="h-4 w-4" />} label="Bando" href={tournament.bulletin_url} />
                      ) : null}
                      {!tournament.is_registration_closed ? (
                        <Button
                          onClick={(event) => {
                            event.stopPropagation();
                            setRegistrationTournamentId(tournament.id);
                          }}
                          size="sm"
                          variant="secondary"
                        >
                          Iscriviti
                        </Button>
                      ) : null}
                    </div>
                    <div className="flex flex-wrap gap-2 text-sm text-[var(--muted-foreground)] md:justify-end">
                      {tournament.can_manage ? <InfoChip icon={<LockKeyhole className="h-4 w-4" />} label="Gestibile" /> : null}
                      <InfoChip icon={timeControlIcon(tournament.time_control_category)} label={tournament.time_control} />
                      <InfoChip
                        icon={tournament.type === "team" ? <Users className="h-4 w-4" /> : <User className="h-4 w-4" />}
                        label={`${tournament.type === "team" ? tournament.teams_count : tournament.players_count} ${tournament.type === "team" ? "squadre" : "giocatori"}`}
                      />
                      <InfoChip icon={<Hash className="h-4 w-4" />} label={`${tournament.rounds_count} turni`} />
                    </div>
                  </div>
                </CardContent>
              </Card>
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

function InfoChip({ icon, label, href }: { icon: ReactNode; label: string; href?: string }) {
  const content = (
    <>
      <span className="text-[var(--muted-foreground)]">{icon}</span>
      <span>{label}</span>
    </>
  );

  if (href) {
    return (
      <a
        className="inline-flex items-center gap-2 rounded-full border bg-white px-3 py-2 hover:bg-[var(--muted)]"
        href={href}
        target="_blank"
        rel="noreferrer"
      >
        {content}
      </a>
    );
  }

  return <div className="inline-flex items-center gap-2 rounded-full border bg-white px-3 py-2">{content}</div>;
}

function DetailHighlightCard({ icon, label, value }: { icon: ReactNode; label: string; value: string }) {
  return (
    <div className="flex h-full items-start gap-3 rounded-2xl border bg-[var(--muted)] px-4 py-4">
      <div className="rounded-xl border bg-white p-2 text-[var(--muted-foreground)]">{icon}</div>
      <div className="min-w-0">
        <div className="text-sm text-[var(--muted-foreground)]">{label}</div>
        <div className="mt-1 text-base font-medium text-[var(--foreground)]">{value}</div>
      </div>
    </div>
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

function timeControlIcon(category: string) {
  if (category === "blitz") return <Zap className="h-4 w-4" />;
  if (category === "rapid") return <Clock3 className="h-4 w-4" />;
  return <Turtle className="h-4 w-4" />;
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
  const normalizedQuery = normalizeSearch(query)
  if (!normalizedQuery) {
    return tournaments
  }

  const queryTerms = normalizedQuery.split(" ").filter(Boolean)
  return tournaments.filter((tournament) => {
    const normalizedName = normalizeSearch(tournament.name)
    return queryTerms.every((term) => normalizedName.includes(term))
  })
}

function normalizeSearch(value: string) {
  return value
    .toLocaleLowerCase()
    .normalize("NFD")
    .replace(/[^\p{L}\p{N}\s]/gu, " ")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/\s+/g, " ")
    .trim()
}
