import { Link, useLocation } from 'react-router-dom'
import type { PropsWithChildren } from 'react'
import { CircleUserRound, Trophy } from 'lucide-react'
import { useAuth } from '@/auth/AuthContext'
import { Button } from '@/components/ui/button'

export function AppShell({ children }: PropsWithChildren) {
  const { user } = useAuth()
  const location = useLocation()
  const showLoginButton = !user && location.pathname !== '/login'
  const showRegisterButton = !user && location.pathname !== '/register'

  return (
    <div className="min-h-screen">
      <header className="border-b bg-white/80 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <Link to="/" className="flex items-center gap-3 text-lg font-semibold">
            <div className="rounded-2xl bg-[var(--primary)] p-2 text-white">
              <Trophy className="h-5 w-5" />
            </div>
            ChessDesk
          </Link>
          <div className="flex items-center gap-3">
            {user ? (
              <div className="text-right text-sm">
                <div className="font-medium">{user.username}</div>
                <div className="text-[var(--muted-foreground)]">{user.email}</div>
              </div>
            ) : null}
            {user ? (
              <Button asChild size="sm" type="button" variant="outline">
                <Link to="/profile" aria-label="Profilo">
                  <CircleUserRound className="h-4 w-4" />
                  Profilo
                </Link>
              </Button>
            ) : showLoginButton ? (
              <Button asChild size="sm" type="button" variant="outline">
                <Link to="/login">Login</Link>
              </Button>
            ) : null}
            {showRegisterButton ? (
              <Button asChild size="sm" type="button">
                <Link to="/register">Registrati</Link>
              </Button>
            ) : null}
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-6 py-8">{children}</main>
    </div>
  )
}
