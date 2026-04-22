export const QueryCacheKeys = {
  tournaments: ["tournaments"] as const,
  tournament: (id: string) => ["tournaments", id] as const,
  players: ["players"] as const,
  fideSearch: (query: string, category?: string) => ["fide-search", category ?? "all", query] as const,
  users: ["users"] as const,
};
