import { BrowserRouter, Route, Routes } from "react-router-dom";
import { TournamentDetailPage } from "@/pages/TournamentDetailPage";
import { TournamentFormPage } from "@/pages/TournamentFormPage";
import { TournamentsPage } from "@/pages/TournamentsPage";
import { NotFoundPage } from "@/pages/NotFoundPage";

export const Router = () => (
  <BrowserRouter>
    <Routes>
      <Route path="/" element={<TournamentsPage />} />
      <Route path="/tournaments" element={<TournamentsPage />} />
      <Route path="/tournaments/new" element={<TournamentFormPage mode="create" />} />
      <Route path="/tournaments/:tournamentId" element={<TournamentDetailPage />} />
      <Route path="/tournaments/:tournamentId/edit" element={<TournamentFormPage mode="edit" />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  </BrowserRouter>
);
