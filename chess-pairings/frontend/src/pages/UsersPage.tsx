import { useState } from 'react'
import { useUsers, useCreateUser, useDeleteUser, useUpdateUser } from '@/api/hooks/users'
import type { User } from '@/api/types'
import { useAuth } from '@/auth/AuthContext'
import { AppShell } from '@/components/layout/AppShell'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { ConfirmDialog } from '@/components/ui/confirm-dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

export function UsersPage() {
  const { user: currentUser } = useAuth()
  const { data: users, isLoading } = useUsers()
  const createUser = useCreateUser()
  const deleteUser = useDeleteUser()
  const updateUser = useUpdateUser()
  const [newEmail, setNewEmail] = useState('')
  const [newUsername, setNewUsername] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [deleteDialogUser, setDeleteDialogUser] = useState<User | null>(null)

  async function handleCreateUser(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    try {
      await createUser.mutateAsync({ email: newEmail, username: newUsername, password: newPassword })
      setNewEmail('')
      setNewUsername('')
      setNewPassword('')
    } catch {
      setError('Non sono riuscito a creare l\'utente.')
    }
  }

  return (
    <AppShell>
      <ConfirmDialog
        open={deleteDialogUser !== null}
        title="Elimina account"
        description={deleteDialogUser ? `Vuoi davvero eliminare l'account ${deleteDialogUser.email}? I suoi tornei verranno trasferiti al tuo account admin.` : ''}
        confirmLabel="Elimina account"
        confirmVariant="destructive"
        onCancel={() => setDeleteDialogUser(null)}
        onConfirm={() => {
          if (!deleteDialogUser) return
          void deleteUser.mutateAsync(deleteDialogUser.id).finally(() => setDeleteDialogUser(null))
        }}
      />
      <div className="grid gap-6 lg:grid-cols-[minmax(0,1.2fr)_minmax(0,0.8fr)]">
        <Card>
          <CardHeader>
            <CardTitle>Utenti</CardTitle>
            <CardDescription>Gestisci gli account che possono accedere alla webapp.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {isLoading ? <div className="text-sm text-[var(--muted-foreground)]">Caricamento utenti...</div> : null}
            {users?.map((user) => (
              <UserRow
                currentUserId={currentUser?.id ?? null}
                onRequestDelete={setDeleteDialogUser}
                key={user.id}
                updateUser={updateUser.mutateAsync}
                user={user}
              />
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Crea utente</CardTitle>
            <CardDescription>Gli utenti creati qui hanno ruolo `user` e vedono solo i propri tornei.</CardDescription>
          </CardHeader>
          <CardContent>
            <form className="space-y-4" onSubmit={handleCreateUser}>
              <div className="space-y-2">
                <Label htmlFor="new-username">Username</Label>
                <Input id="new-username" value={newUsername} onChange={(event) => setNewUsername(event.target.value)} required />
              </div>
              <div className="space-y-2">
                <Label htmlFor="new-email">Email</Label>
                <Input id="new-email" type="email" value={newEmail} onChange={(event) => setNewEmail(event.target.value)} required />
              </div>
              <div className="space-y-2">
                <Label htmlFor="new-password">Password iniziale</Label>
                <Input
                  id="new-password"
                  type="password"
                  value={newPassword}
                  onChange={(event) => setNewPassword(event.target.value)}
                  minLength={8}
                  required
                />
              </div>
              {error ? <div className="text-sm text-red-600">{error}</div> : null}
              <Button className="w-full" disabled={createUser.isPending} type="submit">
                {createUser.isPending ? 'Creazione...' : 'Crea account'}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </AppShell>
  )
}

function UserRow({
  currentUserId,
  onRequestDelete,
  user,
  updateUser,
}: {
  currentUserId: number | null
  onRequestDelete: (user: User) => void
  user: User
  updateUser: (payload: { userId: number; username?: string; password?: string; is_active?: boolean }) => Promise<unknown>
}) {
  const [username, setUsername] = useState(user.username)
  const [password, setPassword] = useState('')
  const [isActive, setIsActive] = useState(user.is_active)

  async function handleSave() {
    try {
      await updateUser({
        userId: user.id,
        username,
        password: password || undefined,
        is_active: user.role === 'admin' ? undefined : isActive,
      })
      setPassword('')
    } catch {}
  }

  return (
    <div className="rounded-2xl border p-4">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <div className="font-medium">{user.email}</div>
          <div className="text-sm text-[var(--muted-foreground)]">{user.username}</div>
        </div>
        <div className="flex gap-2">
          <Badge>{user.role}</Badge>
          <Badge className={user.is_active ? '' : 'bg-white border'}>{user.is_active ? 'attivo' : 'disattivato'}</Badge>
        </div>
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        <div className="space-y-2 md:col-span-1">
          <Label>Username</Label>
          <Input value={username} onChange={(event) => setUsername(event.target.value)} />
        </div>
        <div className="space-y-2 md:col-span-1">
          <Label>Nuova password</Label>
          <Input value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Lascia vuoto per non cambiare" type="password" />
        </div>
        <div className="space-y-2 md:col-span-1">
          <Label>Stato</Label>
            <Button className="w-full" disabled={user.role === 'admin'} onClick={() => setIsActive((current) => !current)} type="button" variant={isActive ? 'secondary' : 'outline'}>
              {isActive ? 'Disattiva' : 'Attiva'}
            </Button>
        </div>
      </div>
      <div className="mt-4 flex items-center justify-between gap-3">
        <div className="flex gap-2">
          {currentUserId !== user.id ? (
            <Button onClick={() => onRequestDelete(user)} type="button" variant="destructive">Elimina</Button>
          ) : null}
          <Button onClick={() => void handleSave()} type="button">Salva</Button>
        </div>
      </div>
    </div>
  )
}
