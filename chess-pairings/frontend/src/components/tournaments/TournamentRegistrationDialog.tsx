import { useEffect, useMemo, useState } from 'react'
import { isAxiosError } from 'axios'
import { Search } from 'lucide-react'
import { useFideSearch } from '@/api/hooks/players'
import { usePublicTournamentRegistration } from '@/api/hooks/tournaments'
import type { FidePlayer, TournamentListItem } from '@/api/types'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

type Props = {
  onClose: () => void
  tournament: Pick<TournamentListItem, 'id' | 'name' | 'time_control_category' | 'is_registration_closed'>
}

export function TournamentRegistrationDialog({ onClose, tournament }: Props) {
  const [mode, setMode] = useState<'fide' | 'manual'>('fide')
  const [query, setQuery] = useState('')
  const [page, setPage] = useState(1)
  const [selectedFideId, setSelectedFideId] = useState<string | null>(null)
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [feedback, setFeedback] = useState<string | null>(null)
  const registrationMutation = usePublicTournamentRegistration(String(tournament.id))
  const { data: fidePlayers, isFetching } = useFideSearch(query, tournament.time_control_category)

  const registrationClosed = tournament.is_registration_closed
  const canSubmitManual = firstName.trim().length >= 2 && lastName.trim().length >= 2 && !registrationClosed
  const visibleResults = useMemo(() => fidePlayers ?? [], [fidePlayers])
  const pageSize = 5
  const totalPages = Math.max(1, Math.ceil(visibleResults.length / pageSize))
  const safePage = Math.min(page, totalPages)
  const paginatedResults = visibleResults.slice((safePage - 1) * pageSize, safePage * pageSize)
  const selectedFidePlayer = visibleResults.find((player) => player.fide_id === selectedFideId) ?? null

  useEffect(() => {
    setPage(1)
    setSelectedFideId(null)
  }, [query, mode])

  async function handleRegisterFromFide(player: FidePlayer) {
    setFeedback(null)
    try {
      await registrationMutation.mutateAsync({ fide_id: player.fide_id })
      onClose()
    } catch (error) {
      setFeedback(readErrorMessage(error))
    }
  }

  async function handleManualRegistration() {
    setFeedback(null)
    try {
      await registrationMutation.mutateAsync({ first_name: firstName, last_name: lastName })
      onClose()
    } catch (error) {
      setFeedback(readErrorMessage(error))
    }
  }

  async function handleSubmit() {
    if (mode === 'fide') {
      if (!selectedFidePlayer || registrationClosed) {
        return
      }
      await handleRegisterFromFide(selectedFidePlayer)
      return
    }

    await handleManualRegistration()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4" onClick={onClose}>
      <Card className="w-full max-w-4xl" onClick={(event) => event.stopPropagation()}>
        <CardHeader>
          <CardTitle>Iscriviti a {tournament.name}</CardTitle>
          <CardDescription>
            Puoi cercarti nel catalogo FIDE oppure inserirti manualmente. Se ti inserisci manualmente partirai con rating 1399.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="flex flex-wrap gap-2">
            <Button onClick={() => setMode('fide')} variant={mode === 'fide' ? 'default' : 'outline'}>Ricerca FIDE</Button>
            <Button onClick={() => setMode('manual')} variant={mode === 'manual' ? 'default' : 'outline'}>Inserimento manuale</Button>
          </div>

          {registrationClosed ? <div className="text-sm text-red-400">Le iscrizioni di questo torneo sono chiuse.</div> : null}

          {mode === 'fide' ? (
            <div className="space-y-4">
              <div className="relative max-w-xl">
                <Search className="pointer-events-none absolute left-3 top-3.5 h-4 w-4 text-[var(--muted-foreground)]" />
                <Input className="pl-9" placeholder="Cerca il tuo nome FIDE" value={query} onChange={(event) => setQuery(event.target.value)} />
              </div>
              {query.trim().length >= 2 ? (
                <div className="space-y-3 overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Nome</TableHead>
                        <TableHead>FIDE ID</TableHead>
                        <TableHead>FED</TableHead>
                        <TableHead>Std</TableHead>
                        <TableHead>Rapid</TableHead>
                        <TableHead>Blitz</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {paginatedResults.map((player) => (
                        <TableRow
                          className={selectedFideId === player.fide_id ? 'cursor-pointer bg-slate-200/80' : 'cursor-pointer'}
                          key={player.fide_id}
                          onClick={() => setSelectedFideId(player.fide_id)}
                        >
                          <TableCell className="min-w-56">{player.full_name}</TableCell>
                          <TableCell>{player.fide_id}</TableCell>
                          <TableCell>{player.federation ?? '-'}</TableCell>
                          <TableCell>{player.standard_rating ?? player.rating ?? '-'}</TableCell>
                          <TableCell>{player.rapid_rating ?? '-'}</TableCell>
                          <TableCell>{player.blitz_rating ?? '-'}</TableCell>
                        </TableRow>
                      ))}
                      {!visibleResults.length ? (
                        <TableRow>
                          <TableCell className="text-[var(--muted-foreground)]" colSpan={6}>
                            {isFetching ? 'Ricerca in corso...' : 'Nessun profilo trovato.'}
                          </TableCell>
                        </TableRow>
                      ) : null}
                    </TableBody>
                  </Table>
                  {visibleResults.length > pageSize ? (
                    <div className="flex items-center justify-between gap-3 text-sm">
                      <div className="text-[var(--muted-foreground)]">Pagina {safePage} di {totalPages}</div>
                      <div className="flex gap-2">
                        <Button disabled={safePage <= 1} onClick={() => setPage((current) => Math.max(1, current - 1))} size="sm" variant="outline">Prec.</Button>
                        <Button disabled={safePage >= totalPages} onClick={() => setPage((current) => Math.min(totalPages, current + 1))} size="sm" variant="outline">Succ.</Button>
                      </div>
                    </div>
                  ) : null}
                </div>
              ) : null}
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="registration-last-name">Cognome</Label>
                <Input id="registration-last-name" value={lastName} onChange={(event) => setLastName(event.target.value)} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="registration-first-name">Nome</Label>
                <Input id="registration-first-name" value={firstName} onChange={(event) => setFirstName(event.target.value)} />
              </div>
              <div className="md:col-span-2 flex items-center justify-between gap-3 rounded-2xl border px-4 py-3 text-sm text-[var(--muted-foreground)]">
                <span>Rating iniziale assegnato automaticamente</span>
                <span className="font-semibold text-[var(--foreground)]">1399</span>
              </div>
            </div>
          )}

          <div className="flex items-center justify-between gap-3">
            <div className="text-sm text-[var(--muted-foreground)]">{feedback}</div>
            <div className="flex items-center gap-2">
              <Button
                disabled={mode === 'fide' ? !selectedFidePlayer || registrationClosed || registrationMutation.isPending : !canSubmitManual || registrationMutation.isPending}
                onClick={() => void handleSubmit()}
              >
                Iscriviti
              </Button>
              <Button onClick={onClose} variant="outline">Chiudi</Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

function readErrorMessage(error: unknown) {
  if (isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') return detail
    return error.message || 'Non sono riuscito a completare l\'iscrizione.'
  }
  if (error instanceof Error) return error.message
  return 'Non sono riuscito a completare l\'iscrizione.'
}
