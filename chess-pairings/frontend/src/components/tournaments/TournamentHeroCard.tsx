import type { ReactNode } from "react";
import { CalendarDays, ChartColumn, Clock3, Hash, MapPin, Paperclip, User, Users, Zap, Turtle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

type TournamentHeroCardProps = {
  name: string;
  description?: string | null;
  type: "individual" | "team";
  isPrivate: boolean;
  isOwner: boolean;
  isEloRated: boolean;
  timeControl: string;
  timeControlCategory: string;
  participantsLabel: string;
  roundsLabel: string;
  venueLabel: string;
  datesLabel: string;
  bulletinUrl?: string | null;
  registerButtonLabel?: string;
  onRegister?: () => void;
  registerDisabled?: boolean;
  secondaryActions?: ReactNode;
};

export function TournamentHeroCard({
  name,
  description,
  type,
  isPrivate,
  isOwner,
  isEloRated,
  timeControl,
  timeControlCategory,
  participantsLabel,
  roundsLabel,
  venueLabel,
  datesLabel,
  bulletinUrl,
  registerButtonLabel,
  onRegister,
  registerDisabled = false,
  secondaryActions,
}: TournamentHeroCardProps) {
  return (
    <Card className="overflow-hidden transition-shadow hover:shadow-md">
      <CardHeader>
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="flex flex-wrap items-center gap-3">
            <CardTitle className="text-3xl">{name}</CardTitle>
            {isPrivate ? <Badge>Privato</Badge> : null}
            {isOwner ? <Badge>Owner</Badge> : null}
          </div>
          <div className="flex flex-wrap gap-2 lg:justify-end">
            <InfoChip icon={<ChartColumn className="h-4 w-4" />} label={isEloRated ? "Variazione Elo" : "No variazione Elo"} />
            <InfoChip icon={timeControlIcon(timeControlCategory)} label={timeControl} />
            <InfoChip
              icon={type === "team" ? <Users className="h-4 w-4" /> : <User className="h-4 w-4" />}
              label={`${type === "team" ? "Squadre" : "Individuale"} (${participantsLabel})`}
            />
            <InfoChip icon={<Hash className="h-4 w-4" />} label={roundsLabel} />
          </div>
        </div>
        <CardDescription>{description ?? "Nessuna descrizione disponibile."}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
          <div className="flex flex-wrap items-start gap-6">
            <InlineDetail icon={<MapPin className="h-4 w-4" />} label="Luogo" value={venueLabel} />
            <InlineDetail icon={<CalendarDays className="h-4 w-4" />} label="Date" value={datesLabel} />
            {bulletinUrl ? <InlineDetail icon={<Paperclip className="h-4 w-4" />} label="Bando" value="Apri bando" href={bulletinUrl} /> : null}
          </div>
          <div className="flex flex-wrap gap-2 md:justify-end">
            {onRegister ? (
              <Button
                disabled={registerDisabled}
                onClick={(event) => {
                  event.stopPropagation()
                  onRegister()
                }}
                variant="outline"
              >
                {registerButtonLabel ?? "Iscriviti"}
              </Button>
            ) : null}
            {secondaryActions}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function InfoChip({ icon, label }: { icon: ReactNode; label: string }) {
  return (
    <div className="inline-flex items-center gap-2 rounded-full border bg-white px-2.5 py-1 text-xs">
      <span className="text-[var(--muted-foreground)]">{icon}</span>
      <span className="text-[var(--muted-foreground)]">{label}</span>
    </div>
  );
}

function InlineDetail({ icon, label, value, href }: { icon: ReactNode; label: string; value: string; href?: string }) {
  const content = (
    <>
      <div className="rounded-2xl border bg-white p-2.5 text-slate-500 shadow-sm">{icon}</div>
      <div className="min-w-0">
        <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">{label}</div>
        <div className="mt-1 text-base font-semibold leading-tight text-slate-900">{value}</div>
      </div>
    </>
  );

  if (href) {
    return (
      <a className="flex min-w-0 items-start gap-3" href={href} target="_blank" rel="noreferrer">
        {content}
      </a>
    );
  }

  return <div className="flex min-w-0 items-start gap-3">{content}</div>;
}

function timeControlIcon(category: string) {
  if (category === "blitz") return <Zap className="h-4 w-4" />;
  if (category === "rapid") return <Clock3 className="h-4 w-4" />;
  return <Turtle className="h-4 w-4" />;
}
