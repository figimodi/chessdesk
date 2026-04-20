import { Link } from "react-router-dom";
import type { PropsWithChildren } from "react";
import { Trophy } from "lucide-react";

export function AppShell({ children }: PropsWithChildren) {
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
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-6 py-8">{children}</main>
    </div>
  );
}
