import { BrowserRouter, Navigate, Outlet, Route, Routes, useLocation } from "react-router-dom";
import { useAuth } from '@/auth/AuthContext'
import { ChangePasswordPage } from '@/pages/ChangePasswordPage'
import { ConfirmEmailPage } from '@/pages/ConfirmEmailPage'
import { LoginPage } from '@/pages/LoginPage'
import { ProfilePage } from '@/pages/ProfilePage'
import { RegisterPage } from '@/pages/RegisterPage'
import { TournamentDetailPage } from "@/pages/TournamentDetailPage";
import { TournamentFormPage } from "@/pages/TournamentFormPage";
import { TournamentsPage } from "@/pages/TournamentsPage";
import { NotFoundPage } from "@/pages/NotFoundPage";
import { UsersPage } from '@/pages/UsersPage'

export const Router = () => (
  <BrowserRouter>
    <Routes>
      <Route path="/" element={<TournamentsPage />} />
      <Route path="/tournaments" element={<TournamentsPage />} />
      <Route path="/tournaments/:tournamentId" element={<TournamentDetailPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/confirm-email" element={<ConfirmEmailPage />} />
      <Route element={<ProtectedRoute />}>
        <Route path="/change-password" element={<ChangePasswordPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/tournaments/new" element={<TournamentFormPage mode="create" />} />
        <Route path="/tournaments/:tournamentId/edit" element={<TournamentFormPage mode="edit" />} />
        <Route element={<AdminRoute />}>
          <Route path="/users" element={<UsersPage />} />
        </Route>
      </Route>
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  </BrowserRouter>
);

function ProtectedRoute() {
  const { isAuthenticated, isLoading, user } = useAuth()
  const location = useLocation()

  if (isLoading) {
    return <div className="flex min-h-screen items-center justify-center text-sm text-[var(--muted-foreground)]">Caricamento sessione...</div>
  }

  if (!isAuthenticated) {
    return <Navigate replace state={{ from: location }} to="/login" />
  }

  if (user?.must_change_password && location.pathname !== '/change-password') {
    return <Navigate replace to="/change-password" />
  }

  return <Outlet />
}

function AdminRoute() {
  const { user } = useAuth()
  if (user?.role !== 'admin') {
    return <Navigate replace to="/" />
  }
  return <Outlet />
}
