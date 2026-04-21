import { Link } from 'react-router-dom'
import type { PropsWithChildren } from 'react'
import { LogOut, Shield, Trophy } from 'lucide-react'
import { useAuth } from '@/auth/AuthContext'
import { Button } from '@/components/ui/button'

export function AppShell({ children }: PropsWithChildren) {
  const { logout, user } = useAuth()

  return (
    <div className="min-h-screen">
      <header className="border-b bg-white/80 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <Link to="/" className="flex items-center gap-3 text-lg font-semibold">
            <div className="rounded-2xl bg-[var(--primary)] p-2 text-white">
              <Trophy className="h-5 w-5" />
            </div>
            Chess Pairings
          </Link>
          <div className="flex items-center gap-3">
            {user ? (
              <div className="text-right text-sm">
                <div className="font-medium">{user.username}</div>
                <div className="text-[var(--muted-foreground)]">{user.email}</div>
              </div>
            ) : null}
            {user ? (
              <Button onClick={logout} size="sm" type="button" variant="outline">
                <LogOut className="h-4 w-4" />
                Esci
              </Button>
            ) : (
              <Button asChild size="sm" type="button" variant="outline">
                <Link to="/login">Login</Link>
              </Button>
            )}
            {user?.role === 'admin' ? (
              <Button asChild size="sm" variant="secondary">
                <Link to="/users">
                  <Shield className="h-4 w-4" />
                  Utenti
                </Link>
              </Button>
            ) : null}
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-6 py-8">{children}</main>
    </div>
  )
}
