import { useState, type FormEvent } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '@/auth/AuthContext'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

export function LoginPage() {
  const { isAuthenticated, login, user } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  if (isAuthenticated) {
    if (user?.must_change_password) {
      return <Navigate replace to="/change-password" />
    }
    return <Navigate replace to="/" />
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setIsSubmitting(true)
    try {
      const loggedUser = await login(username, password)
      if (loggedUser.must_change_password) {
        navigate('/change-password', { replace: true })
        return
      }
      const redirectPath = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname ?? '/'
      navigate(redirectPath, { replace: true })
    } catch {
      setError('Username o password non validi.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[var(--muted)] px-6 py-10">
      <Card className="w-full max-w-md border-0 shadow-lg">
        <CardHeader>
          <CardTitle>Accedi a Chessdesk</CardTitle>
          <CardDescription>Inserisci le credenziali del tuo account per gestire i tornei.</CardDescription>
        </CardHeader>
        <CardContent>
          <form className="space-y-5" onSubmit={handleSubmit}>
            <div className="space-y-2">
              <Label htmlFor="username">Username</Label>
              <Input id="username" value={username} onChange={(event) => setUsername(event.target.value)} required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input id="password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} required />
            </div>
            {error ? <div className="text-sm text-red-600">{error}</div> : null}
            <Button className="w-full" disabled={isSubmitting} type="submit">
              {isSubmitting ? 'Accesso in corso...' : 'Accedi'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
