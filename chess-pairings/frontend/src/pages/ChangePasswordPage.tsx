import { isAxiosError } from 'axios'
import { useState, type FormEvent } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '@/auth/AuthContext'
import { AlertCard } from '@/components/ui/alert-card'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

export function ChangePasswordPage() {
  const { changePassword, isAuthenticated, isLoading, user } = useAuth()
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  if (!isLoading && !isAuthenticated) {
    return <Navigate replace to="/login" />
  }

  if (user && !user.must_change_password) {
    return <Navigate replace to="/" />
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    if (newPassword !== confirmPassword) {
      setError('Le nuove password non coincidono.')
      return
    }
    setIsSubmitting(true)
    try {
      await changePassword(currentPassword, newPassword)
    } catch (submissionError) {
      setError(readErrorMessage(submissionError))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[var(--muted)] px-6 py-10">
      {error ? <AlertCard message={error} onClose={() => setError(null)} /> : null}
      <Card className="w-full max-w-md border-0 shadow-lg">
        <CardHeader>
          <CardTitle>Cambia password</CardTitle>
          <CardDescription>Al primo accesso devi sostituire la password iniziale assegnata dall'amministratore.</CardDescription>
        </CardHeader>
        <CardContent>
          <form className="space-y-5" onSubmit={handleSubmit}>
            <div className="space-y-2">
              <Label htmlFor="current-password">Password attuale</Label>
              <Input id="current-password" type="password" value={currentPassword} onChange={(event) => setCurrentPassword(event.target.value)} required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="new-password">Nuova password</Label>
              <Input id="new-password" type="password" value={newPassword} onChange={(event) => setNewPassword(event.target.value)} required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="confirm-password">Conferma nuova password</Label>
              <Input id="confirm-password" type="password" value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} required />
            </div>
            <Button className="w-full" disabled={isSubmitting} type="submit">
              {isSubmitting ? 'Aggiornamento...' : 'Aggiorna password'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}

function readErrorMessage(error: unknown) {
  if (isAxiosError(error)) {
    const message = error.response?.data?.message
    if (typeof message === 'string') return message
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') return detail
  }
  return 'Non sono riuscito ad aggiornare la password.'
}
