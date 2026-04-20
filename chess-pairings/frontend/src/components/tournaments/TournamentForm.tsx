import { useEffect, useMemo, useState, type ReactNode } from "react";
import { ArrowDown, ArrowUp } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import type { TournamentCreate } from "@/api/types";

const individualTieBreakOptions = [
  { value: "buchholz_cut1", label: "Buchholz Cut 1" },
  { value: "buchholz", label: "Buchholz Total" },
  { value: "sonneborn_berger", label: "Sonneborn-Berger" },
  { value: "direct_encounter", label: "Direct Encounter" },
  { value: "wins_black", label: "Greater Number of Wins / Games with Black" },
];

const teamTieBreakOptions = [
  { value: "individual_points", label: "Punti individuali" },
  { value: "head_to_head", label: "Classifica avulsa" },
  { value: "weighted_sonneborn", label: "Sonneborn pesato" },
];

const individualDefaultTieBreaks = ["buchholz_cut1", "buchholz", "sonneborn_berger"];
const teamDefaultTieBreaks = ["individual_points", "head_to_head", "weighted_sonneborn"];

type Props = {
  value: TournamentCreate;
  onChange: (value: TournamentCreate) => void;
  minimumRoundsCount?: number;
  onRoundsCountValidityChange?: (isValid: boolean) => void;
};

export function TournamentForm({ value, onChange, minimumRoundsCount = 1, onRoundsCountValidityChange }: Props) {
  const rounds = useMemo(() => Array.from({ length: value.rounds_count }, (_, index) => index), [value.rounds_count]);
  const tieBreakOptions = value.type === "team" ? teamTieBreakOptions : individualTieBreakOptions;
  const [minutes, setMinutes] = useState(extractMinutes(value.time_control));
  const [increment, setIncrement] = useState(extractIncrement(value.time_control));
  const [roundsCountInput, setRoundsCountInput] = useState(String(value.rounds_count));
  const [scheduleEnabled, setScheduleEnabled] = useState(value.round_schedule.some(Boolean));

  useEffect(() => {
    setMinutes(extractMinutes(value.time_control));
    setIncrement(extractIncrement(value.time_control));
  }, [value.time_control]);

  useEffect(() => {
    setRoundsCountInput(String(value.rounds_count));
  }, [value.rounds_count]);

  useEffect(() => {
    setScheduleEnabled(value.round_schedule.some(Boolean));
  }, [value.round_schedule]);

  const isRoundsCountInputValid = useMemo(() => {
    const parsed = Number(roundsCountInput);
    return Number.isInteger(parsed) && parsed >= minimumRoundsCount && parsed <= 30;
  }, [minimumRoundsCount, roundsCountInput]);

  useEffect(() => {
    onRoundsCountValidityChange?.(isRoundsCountInputValid);
  }, [isRoundsCountInputValid, onRoundsCountValidityChange]);

  useEffect(() => {
    const allowedTieBreaks = new Set(tieBreakOptions.map((option) => option.value));
    const normalizedTieBreaks = value.tie_breaks.filter((item) => allowedTieBreaks.has(item));
    const defaultTieBreaks = value.type === "team" ? teamDefaultTieBreaks : individualDefaultTieBreaks;

    if (
      normalizedTieBreaks.length !== value.tie_breaks.length ||
      (normalizedTieBreaks.length === 0 && value.tie_breaks.join("|") !== defaultTieBreaks.join("|"))
    ) {
      onChange({
        ...value,
        tie_breaks: normalizedTieBreaks.length ? normalizedTieBreaks : defaultTieBreaks,
      });
    }
  }, [onChange, tieBreakOptions, value]);

  const updateTimeControl = (nextMinutes: string, nextIncrement: string) => {
    const safeMinutes = nextMinutes === "" ? "0" : nextMinutes;
    const safeIncrement = nextIncrement === "" ? "0" : nextIncrement;
    onChange({ ...value, time_control: `${safeMinutes}+${safeIncrement}` });
  };

  const updateRoundsCount = (rawValue: string) => {
    setRoundsCountInput(rawValue);
    const parsed = Number(rawValue);
    if (!Number.isInteger(parsed) || parsed < minimumRoundsCount) {
      return;
    }

    onChange({
      ...value,
      rounds_count: parsed,
      round_schedule: Array.from({ length: parsed }, (_, index) => value.round_schedule[index] ?? ""),
    });
  };

  return (
    <div className="grid gap-5 md:grid-cols-2">
      <Field label="Nome torneo">
        <Input value={value.name} onChange={(event) => onChange({ ...value, name: event.target.value })} />
      </Field>
      <Field label="Sede">
        <Input value={value.venue ?? ""} onChange={(event) => onChange({ ...value, venue: event.target.value })} />
      </Field>
      <Field label="Tipo torneo">
        <select
          className="h-10 w-full rounded-xl border bg-white px-3 text-sm"
          value={value.type}
          onChange={(event) => {
            const nextType = event.target.value as TournamentCreate["type"];
            onChange({
              ...value,
              type: nextType,
              tie_breaks: nextType === "team" ? teamDefaultTieBreaks : individualDefaultTieBreaks,
              max_players_per_team: nextType === "team" ? (value.max_players_per_team ?? 6) : null,
              boards_per_match: nextType === "team" ? (value.boards_per_match ?? 4) : null,
              enforce_board_order: nextType === "team" ? value.enforce_board_order : false,
              match_points_win: nextType === "team" ? (value.match_points_win ?? 2) : null,
              match_points_draw: nextType === "team" ? (value.match_points_draw ?? 1) : null,
              match_points_loss: nextType === "team" ? (value.match_points_loss ?? 0) : null,
            });
          }}
        >
          <option value="individual">Individuale</option>
          <option value="team">A squadre</option>
        </select>
      </Field>
      <div className="grid gap-3 sm:grid-cols-2">
        <Field label="Tempo">
          <Input
            type="number"
            min={0}
            inputMode="numeric"
            value={minutes}
            onChange={(event) => {
              const nextValue = event.target.value;
              setMinutes(nextValue);
              updateTimeControl(nextValue, increment);
            }}
            placeholder="90"
          />
        </Field>
        <Field label="Incremento">
          <Input
            type="number"
            min={0}
            inputMode="numeric"
            value={increment}
            onChange={(event) => {
              const nextValue = event.target.value;
              setIncrement(nextValue);
              updateTimeControl(minutes, nextValue);
            }}
            placeholder="30"
          />
        </Field>
      </div>
      <Field label="Data inizio">
        <Input type="date" value={value.start_date} onChange={(event) => onChange({ ...value, start_date: event.target.value })} />
      </Field>
      <Field label="Data fine">
        <Input type="date" value={value.end_date} onChange={(event) => onChange({ ...value, end_date: event.target.value })} />
      </Field>
      <Field label="Numero turni">
        <div className="space-y-2">
          <Input
            type="number"
            min={minimumRoundsCount}
            max={30}
            inputMode="numeric"
            value={roundsCountInput}
            onChange={(event) => updateRoundsCount(event.target.value)}
          />
          {!isRoundsCountInputValid ? <div className="text-sm text-red-600">Non puoi impostare meno di {minimumRoundsCount} turni.</div> : null}
        </div>
      </Field>
      <Field label="Sistema abbinamenti">
        <select
          className="h-10 w-full rounded-xl border bg-white px-3 text-sm"
          value={value.pairings_system}
          onChange={(event) => onChange({ ...value, pairings_system: event.target.value })}
        >
          <option value="dutch">Swiss Dutch</option>
          <option value="burstein">Swiss Burstein</option>
        </select>
      </Field>
      {value.type === "team" ? (
        <>
          <Field label="Max giocatori per squadra">
            <Input
              type="number"
              min={1}
              inputMode="numeric"
              value={value.max_players_per_team ?? ""}
              onChange={(event) => onChange({ ...value, max_players_per_team: event.target.value === "" ? null : Number(event.target.value) })}
            />
          </Field>
          <Field label="Giocatori schierati per incontro">
            <Input
              type="number"
              min={1}
              inputMode="numeric"
              value={value.boards_per_match ?? ""}
              onChange={(event) => onChange({ ...value, boards_per_match: event.target.value === "" ? null : Number(event.target.value) })}
            />
          </Field>
          <div className="md:col-span-2 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <Field label="Punti vittoria match">
              <Input
                type="number"
                min={0}
                inputMode="numeric"
                value={value.match_points_win ?? ""}
                onChange={(event) => onChange({ ...value, match_points_win: event.target.value === "" ? null : Number(event.target.value) })}
              />
            </Field>
            <Field label="Punti pareggio match">
              <Input
                type="number"
                min={0}
                inputMode="numeric"
                value={value.match_points_draw ?? ""}
                onChange={(event) => onChange({ ...value, match_points_draw: event.target.value === "" ? null : Number(event.target.value) })}
              />
            </Field>
            <Field label="Punti sconfitta match">
              <Input
                type="number"
                min={0}
                inputMode="numeric"
                value={value.match_points_loss ?? ""}
                onChange={(event) => onChange({ ...value, match_points_loss: event.target.value === "" ? null : Number(event.target.value) })}
              />
            </Field>
            <Field label="Ordine di scacchiera">
              <select
                className="h-10 w-full rounded-xl border bg-white px-3 text-sm"
                value={value.enforce_board_order ? "fixed" : "free"}
                onChange={(event) => onChange({ ...value, enforce_board_order: event.target.value === "fixed" })}
              >
                <option value="fixed">Da mantenere</option>
                <option value="free">Libero</option>
              </select>
            </Field>
          </div>
        </>
      ) : null}
      <Field label="Variazione Elo">
        <label className="inline-flex items-center gap-2 text-sm font-medium">
          <input type="checkbox" checked={value.is_elo_rated} onChange={(event) => onChange({ ...value, is_elo_rated: event.target.checked })} />
          Calcola variazione Elo del torneo
        </label>
      </Field>
      <div className="md:col-span-2 space-y-3">
        <Label>Criteri di spareggio</Label>
        <div className="space-y-2">
          {value.tie_breaks.map((tieBreak, index) => (
            <div key={`${tieBreak}-${index}`} className="flex flex-wrap items-center gap-2 rounded-xl border bg-white px-3 py-2">
              <div className="w-6 text-sm text-[var(--muted-foreground)]">{index + 1}.</div>
              <select
                className="h-10 min-w-0 flex-1 rounded-xl border bg-white px-3 text-sm"
                value={tieBreak}
                onChange={(event) => {
                  const nextTieBreaks = [...value.tie_breaks];
                  nextTieBreaks[index] = event.target.value;
                  onChange({ ...value, tie_breaks: nextTieBreaks.filter((item, itemIndex) => nextTieBreaks.indexOf(item) === itemIndex) });
                }}
              >
                {tieBreakOptions.map((option) => (
                  <option key={option.value} value={option.value} disabled={value.tie_breaks.includes(option.value) && option.value !== tieBreak}>
                    {option.label}
                  </option>
                ))}
              </select>
              <div className="flex items-center gap-1">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  disabled={index === 0}
                  onClick={() => {
                    if (index === 0) return;
                    const nextTieBreaks = [...value.tie_breaks];
                    [nextTieBreaks[index - 1], nextTieBreaks[index]] = [nextTieBreaks[index], nextTieBreaks[index - 1]];
                    onChange({ ...value, tie_breaks: nextTieBreaks });
                  }}
                >
                  <ArrowUp className="h-4 w-4" />
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  disabled={index === value.tie_breaks.length - 1}
                  onClick={() => {
                    if (index === value.tie_breaks.length - 1) return;
                    const nextTieBreaks = [...value.tie_breaks];
                    [nextTieBreaks[index], nextTieBreaks[index + 1]] = [nextTieBreaks[index + 1], nextTieBreaks[index]];
                    onChange({ ...value, tie_breaks: nextTieBreaks });
                  }}
                >
                  <ArrowDown className="h-4 w-4" />
                </Button>
                <Button
                  type="button"
                  variant="destructive"
                  size="sm"
                  disabled={value.tie_breaks.length <= 1}
                  onClick={() => {
                    if (value.tie_breaks.length <= 1) return;
                    onChange({
                      ...value,
                      tie_breaks: value.tie_breaks.filter((_, itemIndex) => itemIndex !== index),
                    });
                  }}
                >
                  Rimuovi
                </Button>
              </div>
            </div>
          ))}
        </div>
        <button
          type="button"
          className="text-sm font-medium text-[var(--primary)]"
          onClick={() => {
            const nextOption = tieBreakOptions.find((option) => !value.tie_breaks.includes(option.value));
            if (!nextOption) return;
            onChange({ ...value, tie_breaks: [...value.tie_breaks, nextOption.value] });
          }}
        >
          + Aggiungi spareggio
        </button>
      </div>
      <div className="md:col-span-2">
        <Field label="Descrizione">
          <Textarea value={value.description ?? ""} onChange={(event) => onChange({ ...value, description: event.target.value })} />
        </Field>
      </div>
      <div className="md:col-span-2 space-y-3">
        <label className="inline-flex items-center gap-2 text-sm font-medium">
          <input
            type="checkbox"
            checked={scheduleEnabled}
            onChange={(event) => {
              const enabled = event.target.checked;
              setScheduleEnabled(enabled);
              if (!enabled) {
                onChange({ ...value, round_schedule: Array.from({ length: value.rounds_count }, () => "") });
              }
            }}
          />
          Calendario Eventi
        </label>
        {scheduleEnabled ? (
          <div className="space-y-3">
            {rounds.map((round) => (
              <Field key={round} label={`Turno ${round + 1}`}>
                <Input
                  className="max-w-xs"
                  type="datetime-local"
                  value={value.round_schedule[round] ?? ""}
                  onChange={(event) => {
                    const schedule = [...value.round_schedule];
                    schedule[round] = event.target.value;
                    onChange({ ...value, round_schedule: schedule });
                  }}
                />
              </Field>
            ))}
          </div>
        ) : null}
      </div>
    </div>
  );
}

function extractMinutes(timeControl: string) {
  const [minutes] = timeControl.split("+");
  return minutes ?? "0";
}

function extractIncrement(timeControl: string) {
  const [, increment = "0"] = timeControl.split("+");
  return increment;
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      {children}
    </div>
  );
}
