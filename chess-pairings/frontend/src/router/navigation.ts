export const ROUTES = {
  HOME: "/",
  TOURNAMENT_NEW: "/tournaments/new",
  TOURNAMENT_DETAIL: (id: string) => `/tournaments/${id}`,
  TOURNAMENT_EDIT: (id: string) => `/tournaments/${id}/edit`,
} as const;
