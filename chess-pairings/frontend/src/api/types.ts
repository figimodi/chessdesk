export type TournamentType = "individual" | "team";
export type TournamentFormat = "swiss";
export type PairingResult = "1-0" | "0-1" | "1/2-1/2" | "1-0F" | "0-1F" | "0F-0F" | "1F-1F" | "1-bye" | "unplayed";

export type TournamentListItem = {
  id: number;
  name: string;
  type: TournamentType;
  format: TournamentFormat;
  time_control: string;
  start_date: string;
  end_date: string;
  rounds_count: number;
  pairings_system: string;
  tie_breaks: string[];
  is_elo_rated: boolean;
  max_players_per_team?: number | null;
  boards_per_match?: number | null;
  enforce_board_order: boolean;
  match_points_win?: number | null;
  match_points_draw?: number | null;
  match_points_loss?: number | null;
  time_control_category: string;
  venue?: string | null;
  description?: string | null;
  is_published: boolean;
  is_private: boolean;
  is_registration_closed: boolean;
  bulletin_url?: string | null;
  players_count: number;
  teams_count: number;
  can_manage: boolean;
  owner_id?: number | null;
};

export type TournamentPlayer = {
  player_id: number;
  tournament_id: number;
  team_id?: number | null;
  team_board_order?: number | null;
  seed_number?: number | null;
  initial_rating?: number | null;
  start_round_number: number;
  is_active: boolean;
  full_name: string;
  fide_id?: string | null;
  federation?: string | null;
  rating?: number | null;
  rapid_rating?: number | null;
  blitz_rating?: number | null;
  birth_year?: number | null;
  availability_by_round: boolean[];
  team_name?: string | null;
};

export type StandingEntry = {
  player_id: number;
  full_name: string;
  federation?: string | null;
  team_board_order?: number | null;
  seed_number?: number | null;
  rating?: number | null;
  rapid_rating?: number | null;
  blitz_rating?: number | null;
  team_id?: number | null;
  team_name?: string | null;
  points: number;
  buchholz: number;
  buchholz_cut1: number;
  sonneborn_berger: number;
  average_opponent_rating?: number | null;
  performance_rating?: number | null;
  elo_change?: number | null;
  played_games: number;
  wins: number;
  black_wins: number;
};

export type Pairing = {
  id: number;
  match_number?: number | null;
  board_number: number;
  white_player_id: number;
  black_player_id?: number | null;
  white_player_name: string;
  black_player_name?: string | null;
  white_team_id?: number | null;
  black_team_id?: number | null;
  white_team_name?: string | null;
  black_team_name?: string | null;
  result: PairingResult;
  white_points: number;
  black_points: number;
  is_bye: boolean;
};

export type Round = {
  id: number;
  number: number;
  scheduled_at?: string | null;
  status: string;
  pairings: Pairing[];
};

export type Team = {
  id: number;
  tournament_id: number;
  name: string;
  is_active: boolean;
  availability_by_round: boolean[];
  points: number;
  members_count: number;
  members: TeamMember[];
};

export type TeamMember = {
  player_id: number;
  full_name: string;
  federation?: string | null;
  seed_number?: number | null;
  rating?: number | null;
  rapid_rating?: number | null;
  blitz_rating?: number | null;
  birth_year?: number | null;
  team_board_order?: number | null;
  selected_by_round: boolean[];
};

export type TeamStandingEntry = {
  team_id: number;
  name: string;
  match_points: number;
  individual_points: number;
  head_to_head_applies: boolean;
  head_to_head_match_points: number;
  head_to_head_individual_points: number;
  weighted_sonneborn: number;
};

export type TournamentDetail = TournamentListItem & {
  rounds: Round[];
  standings: StandingEntry[];
  team_standings: TeamStandingEntry[];
  players: TournamentPlayer[];
  teams: Team[];
};

export type TournamentCreate = {
  name: string;
  type: TournamentType;
  format: TournamentFormat;
  time_control: string;
  start_date: string;
  end_date: string;
  rounds_count: number;
  pairings_system: string;
  tie_breaks: string[];
  is_elo_rated: boolean;
  max_players_per_team?: number | null;
  boards_per_match?: number | null;
  enforce_board_order: boolean;
  match_points_win?: number | null;
  match_points_draw?: number | null;
  match_points_loss?: number | null;
  venue?: string;
  description?: string;
  is_published: boolean;
  is_private: boolean;
  owner_id?: number | null;
  round_schedule: string[];
};

export type TournamentUpdate = Partial<TournamentCreate>;

export type Player = {
  id: number;
  full_name: string;
  fide_id?: string | null;
  federation?: string | null;
  rating?: number | null;
  rapid_rating?: number | null;
  blitz_rating?: number | null;
  fide_title?: string | null;
};

export type FidePlayer = {
  fide_id: string;
  full_name: string;
  federation?: string | null;
  rating?: number | null;
  standard_rating?: number | null;
  rapid_rating?: number | null;
  blitz_rating?: number | null;
  birth_year?: number | null;
  fide_title?: string | null;
};

export type UserRole = 'admin' | 'user'

export type User = {
  id: number
  email: string
  username: string
  role: UserRole
  is_active: boolean
  email_confirmed: boolean
  must_change_password: boolean
}

export type AuthToken = {
  access_token: string
  token_type: 'bearer'
  user: User
}

export type UserCreate = {
  email: string
  username: string
  password: string
}

export type UserUpdate = {
  username?: string
  password?: string
  is_active?: boolean
}

export type TournamentPublicRegistration = {
  fide_id?: string
  first_name?: string
  last_name?: string
}

export type PublicTeamRegistrationCreate = {
  team_name: string
  captain: TournamentPublicRegistration
  teammate_player_ids: number[]
  teammate_fide_ids: string[]
  teammate_manual_entries: TournamentPublicRegistration[]
}

export type PublicTeamRegistrationJoin = {
  team_id: number
  pin: string
  registrant: TournamentPublicRegistration
}

export type PublicTeamRegistrationCreateResponse = {
  team_id: number
  team_name: string
  pin: string
  members_count: number
}

export type PasswordChangeRequest = {
  current_password: string
  new_password: string
}

export type PublicRegistrationRequest = {
  email: string
  username: string
  password: string
}

export type EmailConfirmationRequest = {
  token: string
}

export type EmailConfirmationResendRequest = {
  email: string
}

export type MessageResponse = {
  message: string
}
