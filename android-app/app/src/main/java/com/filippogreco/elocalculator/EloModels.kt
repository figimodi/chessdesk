package com.filippogreco.elocalculator

enum class RatingType(val label: String) {
    STANDARD("Standard"),
    RAPID("Rapid"),
    BLITZ("Blitz")
}

enum class MatchResult(val label: String, val score: Double?) {
    NOT_PLAYED("TBD", null),
    WIN("W", 1.0),
    DRAW("D", 0.5),
    LOSS("L", 0.0)
}

data class FidePlayer(
    val id: String,
    val name: String,
    val federation: String,
    val standardRating: Int?,
    val rapidRating: Int?,
    val blitzRating: Int?,
    val birthYear: String,
) {
    fun ratingFor(type: RatingType): Int? = when (type) {
        RatingType.STANDARD -> standardRating
        RatingType.RAPID -> rapidRating
        RatingType.BLITZ -> blitzRating
    }
}

data class SelectedOpponent(
    val player: FidePlayer,
    val result: MatchResult = MatchResult.NOT_PLAYED,
)

data class EloDelta(
    val win: Double,
    val draw: Double,
    val loss: Double,
)

data class RankBucket(
    val activePlayers: String = "-",
    val allPlayers: String = "-",
)

data class PlayerRanks(
    val world: RankBucket = RankBucket(),
    val nationalLabel: String = "National Rank",
    val national: RankBucket = RankBucket(),
    val continentLabel: String = "Continent Rank",
    val continent: RankBucket = RankBucket(),
)

data class PlayerStats(
    val totalGames: String = "-",
    val standardGames: String = "-",
    val rapidGames: String = "-",
    val blitzGames: String = "-",
)

data class RatingHistoryEntry(
    val period: String,
    val standardRating: String,
    val standardGames: String,
    val rapidRating: String,
    val rapidGames: String,
    val blitzRating: String,
    val blitzGames: String,
)

data class FideProfile(
    val player: FidePlayer,
    val fullName: String,
    val federationName: String,
    val gender: String,
    val fideTitle: String,
    val worldChessProfileUrl: String? = null,
    val titleAwardedYear: String? = null,
    val ranks: PlayerRanks = PlayerRanks(),
    val stats: PlayerStats = PlayerStats(),
    val history: List<RatingHistoryEntry> = emptyList(),
)

enum class AppPage(val label: String) {
    PROFILE("Profile"),
    PLAYERS("Players"),
    HISTORY("History"),
    STATS("Stats"),
    CALCULATOR("Calculator"),
}

enum class ViewedPlayerPage(val label: String) {
    PROFILE("Profile"),
    STATS("Stats"),
    HISTORY("History"),
}

data class EloUiState(
    val selfQuery: String = "",
    val kFactor: String = "20",
    val opponentQuery: String = "",
    val ratingType: RatingType = RatingType.STANDARD,
    val isLoading: Boolean = false,
    val isLoadingSelf: Boolean = false,
    val errorMessage: String? = null,
    val selfErrorMessage: String? = null,
    val playerLookupErrorMessage: String? = null,
    val selfSearchResults: List<FidePlayer> = emptyList(),
    val selectedSelf: FidePlayer? = null,
    val profile: FideProfile? = null,
    val searchResults: List<FidePlayer> = emptyList(),
    val playerLookupQuery: String = "",
    val playerLookupResults: List<FidePlayer> = emptyList(),
    val viewedPlayerProfile: FideProfile? = null,
    val viewedPlayerPage: ViewedPlayerPage = ViewedPlayerPage.PROFILE,
    val selectedOpponents: List<SelectedOpponent> = emptyList(),
    val currentPage: AppPage = AppPage.PROFILE,
    val hasPersistedProfile: Boolean = false,
    val isRestoringProfile: Boolean = true,
    val isLoadingProfile: Boolean = false,
    val isLoadingPlayerLookup: Boolean = false,
    val isLoadingViewedPlayerProfile: Boolean = false,
    val profileErrorMessage: String? = null,
)
