import { isAxiosError } from 'axios'
import { useEffect, useState, type FormEvent } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { api } from '@/api/client'
import { useAuth } from '@/auth/useAuth'
import { AppShell } from '@/components/layout/AppShell'
import { AlertCard } from '@/components/ui/alert-card'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

export function RegisterPage() {
  const { isAuthenticated, user } = useAuth()
  const [email, setEmail] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [feedback, setFeedback] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isResending, setIsResending] = useState(false)
  const [resendCooldownEndsAt, setResendCooldownEndsAt] = useState<number | null>(null)
  const [cooldownSeconds, setCooldownSeconds] = useState(0)

  useEffect(() => {
    if (!resendCooldownEndsAt) {
      setCooldownSeconds(0)
      return
    }

    const updateCooldown = () => {
      const remaining = Math.max(0, Math.ceil((resendCooldownEndsAt - Date.now()) / 1000))
      setCooldownSeconds(remaining)
      if (remaining === 0) {
        setResendCooldownEndsAt(null)
      }
    }

    updateCooldown()
    const interval = window.setInterval(updateCooldown, 1000)
    return () => window.clearInterval(interval)
  }, [resendCooldownEndsAt])

  if (isAuthenticated) {
    if (user?.must_change_password) {
      return <Navigate replace to="/change-password" />
    }
    return <Navigate replace to="/" />
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setFeedback(null)
    if (password !== confirmPassword) {
      setError('Le password non coincidono.')
      return
    }

    setIsSubmitting(true)
    try {
      const response = await api.register({ email, username, password })
      setFeedback(response.message)
      setResendCooldownEndsAt(Date.now() + 60_000)
    } catch (submissionError) {
      setError(readErrorMessage(submissionError, 'Non sono riuscito a completare la registrazione.'))
    } finally {
      setIsSubmitting(false)
    }
  }

  async function handleResend() {
    setError(null)
    setFeedback(null)
    setIsResending(true)
    try {
      const response = await api.resendConfirmation({ email })
      setFeedback(response.message)
      setResendCooldownEndsAt(Date.now() + 60_000)
    } catch (submissionError) {
      setError(readErrorMessage(submissionError, 'Non sono riuscito a inviare una nuova email di conferma.'))
    } finally {
      setIsResending(false)
    }
  }

  return (
    <AppShell>
      {error ? <AlertCard message={error} onClose={() => setError(null)} /> : null}
      <div className="flex min-h-[calc(100vh-12rem)] items-center justify-center px-6 py-10">
        <Card className="w-full max-w-md border-0 shadow-lg">
          <CardHeader>
            <CardTitle>Crea un account</CardTitle>
            <CardDescription>Registrati e conferma la tua email per iniziare a usare ChessDesk.</CardDescription>
          </CardHeader>
          <CardContent>
            <form className="space-y-5" onSubmit={handleSubmit}>
              <div className="space-y-2">
                <Label htmlFor="register-email">Email</Label>
                <Input id="register-email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
              </div>
              <div className="space-y-2">
                <Label htmlFor="register-username">Nome utente</Label>
                <Input id="register-username" value={username} onChange={(event) => setUsername(event.target.value)} required />
              </div>
              <div className="space-y-2">
                <Label htmlFor="register-password">Password</Label>
                <Input id="register-password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} required />
              </div>
              <div className="space-y-2">
                <Label htmlFor="register-confirm-password">Conferma password</Label>
                <Input id="register-confirm-password" type="password" value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} required />
              </div>
              {feedback ? <div className="text-sm text-emerald-700">{feedback}</div> : null}
              <Button className="w-full" disabled={isSubmitting} type="submit">
                {isSubmitting ? 'Registrazione...' : 'Registrati'}
              </Button>
            </form>
            <div className="mt-4 flex items-center justify-between gap-3 text-sm">
              <Link className="text-[var(--primary)]" to="/login">
                Hai gia un account? Accedi
              </Link>
              <Button disabled={!email || isResending || cooldownSeconds > 0} onClick={() => void handleResend()} size="sm" type="button" variant="ghost">
                {isResending ? 'Invio...' : cooldownSeconds > 0 ? `Reinvia tra ${cooldownSeconds}s` : 'Reinvia email'}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </AppShell>
  )
}

function readErrorMessage(error: unknown, fallback: string) {
  if (isAxiosError(error)) {
    const message = error.response?.data?.message
    if (typeof message === 'string') return message
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail) && detail.length > 0) {
      const firstIssue = detail[0]
      if (typeof firstIssue?.msg === 'string') {
        const field = Array.isArray(firstIssue?.loc) ? firstIssue.loc[firstIssue.loc.length - 1] : null
        const normalizedMessage = String(firstIssue.msg).replace(/^Value error,\s*/i, '')
        if (field === 'password' && normalizedMessage.toLowerCase().includes('string should have at least')) {
          return 'La password deve contenere almeno 8 caratteri.'
        }
        if (field === 'username' && normalizedMessage.toLowerCase().includes('string should have at least')) {
          return 'Lo username deve contenere almeno 2 caratteri.'
        }
        if (field === 'email') {
          return 'Inserisci un indirizzo email valido.'
        }
        return field ? `${formatFieldLabel(field)}: ${normalizedMessage}` : normalizedMessage
      }
    }
    return error.message || fallback
  }
  if (error instanceof Error) return error.message
  return fallback
}

function formatFieldLabel(field: string) {
  if (field === 'password') return 'Password'
  if (field === 'username') return 'Nome utente'
  if (field === 'email') return 'Email'
  return field
}
