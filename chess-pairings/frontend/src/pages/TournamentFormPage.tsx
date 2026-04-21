import { useEffect, useMemo, useState } from "react";
import { isAxiosError } from "axios";
import { Paperclip } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";
import { useCreateTournament, useTournament, useUpdateTournament } from "@/api/hooks/tournaments";
import { useUploadBulletin } from "@/api/hooks/tournaments";
import { useUsers } from "@/api/hooks/users";
import type { TournamentCreate } from "@/api/types";
import { useAuth } from "@/auth/AuthContext";
import { AppShell } from "@/components/layout/AppShell";
import { TournamentForm } from "@/components/tournaments/TournamentForm";
import { AlertCard } from "@/components/ui/alert-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const emptyForm: TournamentCreate = {
  name: "",
  type: "individual",
  format: "swiss",
  time_control: "90+30",
  start_date: "",
  end_date: "",
  rounds_count: 5,
  pairings_system: "dutch",
  tie_breaks: ["buchholz_cut1", "buchholz", "sonneborn_berger"],
  is_elo_rated: false,
  max_players_per_team: null,
  boards_per_match: null,
  enforce_board_order: false,
  match_points_win: null,
  match_points_draw: null,
  match_points_loss: null,
  venue: "",
  description: "",
  is_published: false,
  is_private: false,
  owner_id: null,
  round_schedule: Array.from({ length: 5 }, () => ""),
};

export function TournamentFormPage({ mode }: { mode: "create" | "edit" }) {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { tournamentId = "" } = useParams();
  const { data, isError } = useTournament(tournamentId);
  const isAdmin = user?.role === "admin";
  const { data: users = [] } = useUsers(isAdmin && mode === "edit");
  const createMutation = useCreateTournament();
  const updateMutation = useUpdateTournament(tournamentId);
  const uploadMutation = useUploadBulletin(tournamentId);
  const minimumRoundsCount = useMemo(() => {
    if (mode !== "edit" || !data) return 1;
    return Math.max(1, data.rounds.filter((round) => round.pairings.length > 0).length);
  }, [data, mode]);

  const initialState = useMemo<TournamentCreate>(() => {
    if (mode === "edit" && data) {
      return {
        name: data.name,
        type: data.type,
        format: data.format,
        time_control: data.time_control,
        start_date: data.start_date,
        end_date: data.end_date,
        rounds_count: data.rounds_count,
        pairings_system: data.pairings_system,
        tie_breaks: data.tie_breaks,
        is_elo_rated: data.is_elo_rated,
        max_players_per_team: data.max_players_per_team ?? null,
        boards_per_match: data.boards_per_match ?? null,
        enforce_board_order: data.enforce_board_order,
        match_points_win: data.match_points_win ?? null,
        match_points_draw: data.match_points_draw ?? null,
        match_points_loss: data.match_points_loss ?? null,
        venue: data.venue ?? "",
        description: data.description ?? "",
        is_published: data.is_published,
        is_private: data.is_private,
        owner_id: data.owner_id ?? null,
        round_schedule: Array.from({ length: data.rounds_count }, (_, index) => data.rounds[index]?.scheduled_at?.slice(0, 16) ?? ""),
      };
    }
    return emptyForm;
  }, [data, mode]);

  const ownerOptions = useMemo(() => users.map((entry) => ({ id: entry.id, label: `${entry.username} (${entry.email})` })), [users]);

  const [form, setForm] = useState<TournamentCreate>(initialState);
  const [alertMessage, setAlertMessage] = useState("");
  const [isRoundsCountValid, setIsRoundsCountValid] = useState(true);

  useEffect(() => {
    setForm(initialState);
  }, [initialState]);

  useEffect(() => {
    setIsRoundsCountValid(true);
  }, [initialState]);

  const handleSubmit = async () => {
    if (!isRoundsCountValid) {
      setAlertMessage(`Non puoi impostare meno di ${minimumRoundsCount} turni.`);
      return;
    }

    const sanitizedForm = {
      ...form,
      round_schedule: form.round_schedule.filter((value) => value.trim() !== ""),
    };

    try {
      if (mode === "create") {
        const tournament = await createMutation.mutateAsync(sanitizedForm);
        navigate(`/tournaments/${tournament.id}`);
        return;
      }
      await updateMutation.mutateAsync(sanitizedForm);
      navigate(`/tournaments/${tournamentId}`);
    } catch (error) {
      setAlertMessage(readErrorMessage(error));
    }
  };

  if (mode === "edit" && isError) {
    return <AppShell>Torneo non trovato o non accessibile.</AppShell>;
  }

  return (
    <AppShell>
      {alertMessage ? <AlertCard message={alertMessage} onClose={() => setAlertMessage("")} /> : null}
      <Card>
        <CardHeader>
          <CardTitle>{mode === "create" ? "Nuovo torneo" : "Modifica torneo"}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <TournamentForm
            value={form}
            onChange={setForm}
            minimumRoundsCount={minimumRoundsCount}
            onRoundsCountValidityChange={setIsRoundsCountValid}
            ownerOptions={ownerOptions}
            showOwnerField={mode === "edit" && isAdmin}
          />
          <div className="flex flex-wrap gap-3">
            <label
              className={`inline-flex items-center gap-2 rounded-xl border bg-white px-4 py-2 text-sm ${mode === "create" ? "cursor-not-allowed opacity-60" : "cursor-pointer"}`}
            >
              Upload bando
              <input
                className="hidden"
                type="file"
                accept="application/pdf"
                disabled={mode === "create"}
                onChange={(event) => {
                  const file = event.target.files?.[0];
                  if (file) uploadMutation.mutate(file);
                }}
              />
            </label>
            {mode === "create" ? (
              <div className="flex items-center text-sm text-[var(--muted-foreground)]">Salva prima il torneo per caricare il bando.</div>
            ) : null}
            {mode === "edit" && data?.bulletin_url ? (
              <Button variant="outline" asChild>
                <a href={data.bulletin_url} target="_blank" rel="noreferrer">
                  <Paperclip className="h-4 w-4" />
                  Apri bando caricato
                </a>
              </Button>
            ) : null}
          </div>
          <div className="flex justify-end gap-3">
            <Button variant="outline" onClick={() => navigate(-1)}>
              Annulla
            </Button>
            <Button onClick={handleSubmit} disabled={!isRoundsCountValid}>
              {mode === "create" ? "Crea torneo" : "Salva"}
            </Button>
          </div>
        </CardContent>
      </Card>
    </AppShell>
  );
}

function readErrorMessage(error: unknown) {
  if (isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail) && detail.length > 0) {
      const firstIssue = detail[0];
      if (typeof firstIssue?.msg === "string") return firstIssue.msg.replace(/^Value error,\s*/i, "");
    }
    if (typeof error.response?.data?.message === "string") return error.response.data.message;
    return error.message;
  }
  if (error instanceof Error) return error.message;
  return "Si e verificato un errore inatteso.";
}
