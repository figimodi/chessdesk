import { isAxiosError } from 'axios'
import { LogOut, Shield } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { useAuth } from '@/auth/useAuth'
import { AppShell } from '@/components/layout/AppShell'
import { AlertCard } from '@/components/ui/alert-card'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

export function ProfilePage() {
  const { changePassword, isAuthenticated, isLoading, logout, user } = useAuth()
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  if (!isLoading && !isAuthenticated) {
    return <Navigate replace to="/login" />
  }

  if (!user) {
    return <AppShell>Caricamento profilo...</AppShell>
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setSuccess(null)
    if (newPassword !== confirmPassword) {
      setError('Le nuove password non coincidono.')
      return
    }
    setIsSubmitting(true)
    try {
      await changePassword(currentPassword, newPassword)
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
      setSuccess('Password aggiornata correttamente.')
    } catch (submissionError) {
      setError(readErrorMessage(submissionError))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <AppShell>
      {error ? <AlertCard message={error} onClose={() => setError(null)} /> : null}
      <div className="grid gap-6 lg:grid-cols-[minmax(0,0.8fr)_minmax(0,1.2fr)]">
        <Card>
          <CardHeader>
            <CardTitle>Profilo</CardTitle>
            <CardDescription>Consulta i dati del tuo account e accedi alle azioni rapide.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-2xl border bg-white p-4">
              <div className="text-sm text-[var(--muted-foreground)]">Nome utente</div>
              <div className="mt-1 font-medium">{user.username}</div>
            </div>
            <div className="rounded-2xl border bg-white p-4">
              <div className="text-sm text-[var(--muted-foreground)]">Email</div>
              <div className="mt-1 font-medium">{user.email}</div>
            </div>
            <div className="flex flex-wrap gap-3">
              {user.role === 'admin' ? (
                <Button asChild variant="outline">
                  <Link to="/users">
                    <Shield className="h-4 w-4" />
                    Utenti
                  </Link>
                </Button>
              ) : null}
              <Button onClick={logout} type="button" variant="outline">
                <LogOut className="h-4 w-4" />
                Esci
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Cambia password</CardTitle>
            <CardDescription>Per confermare la modifica devi inserire la password attuale.</CardDescription>
          </CardHeader>
          <CardContent>
            <form className="space-y-5" onSubmit={handleSubmit}>
              <div className="space-y-2">
                <Label htmlFor="profile-current-password">Password attuale</Label>
                <Input id="profile-current-password" type="password" value={currentPassword} onChange={(event) => setCurrentPassword(event.target.value)} required />
              </div>
              <div className="space-y-2">
                <Label htmlFor="profile-new-password">Nuova password</Label>
                <Input id="profile-new-password" type="password" value={newPassword} onChange={(event) => setNewPassword(event.target.value)} required />
              </div>
              <div className="space-y-2">
                <Label htmlFor="profile-confirm-password">Conferma nuova password</Label>
                <Input id="profile-confirm-password" type="password" value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} required />
              </div>
              {success ? <div className="text-sm text-emerald-700">{success}</div> : null}
              <Button disabled={isSubmitting} type="submit">
                {isSubmitting ? 'Aggiornamento...' : 'Aggiorna password'}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </AppShell>
  )
}

function readErrorMessage(error: unknown) {
  if (isAxiosError(error)) {
    const message = error.response?.data?.message
    if (typeof message === 'string') return message
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') return detail
    return error.message || 'Non sono riuscito ad aggiornare la password.'
  }
  if (error instanceof Error) return error.message
  return 'Non sono riuscito ad aggiornare la password.'
}
