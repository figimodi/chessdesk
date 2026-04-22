import { isAxiosError } from 'axios'
import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { api } from '@/api/client'
import { AppShell } from '@/components/layout/AppShell'
import { AlertCard } from '@/components/ui/alert-card'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export function ConfirmEmailPage() {
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token') ?? ''
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>(token ? 'loading' : 'error')
  const [message, setMessage] = useState(token ? 'Conferma in corso...' : 'Link di conferma non valido.')

  useEffect(() => {
    if (!token) return
    void api
      .confirmEmail({ token })
      .then((response) => {
        setStatus('success')
        setMessage(response.message)
      })
      .catch((error) => {
        setStatus('error')
        setMessage(readErrorMessage(error))
      })
  }, [token])

  return (
    <AppShell>
      {status === 'error' ? <AlertCard message={message} onClose={() => setStatus('success')} /> : null}
      <div className="flex min-h-[calc(100vh-12rem)] items-center justify-center px-6 py-10">
        <Card className="w-full max-w-md border-0 shadow-lg">
          <CardHeader>
            <CardTitle>Conferma email</CardTitle>
            <CardDescription>Completa l'attivazione del tuo account.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            <div className="text-sm text-[var(--foreground)]">{message}</div>
            <Button asChild className="w-full">
              <Link to="/login">Vai al login</Link>
            </Button>
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
    return error.message || 'Non sono riuscito a confermare la tua email.'
  }
  if (error instanceof Error) return error.message
  return 'Non sono riuscito a confermare la tua email.'
}
