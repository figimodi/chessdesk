package com.filippogreco.elocalculator

fun previewPlayer() = FidePlayer(
    id = "1503014",
    name = "Carlsen, Magnus",
    federation = "NOR",
    standardRating = 2830,
    rapidRating = 2819,
    blitzRating = 2883,
    birthYear = "1990",
)

fun previewOpponent() = FidePlayer(
    id = "2020009",
    name = "Nakamura, Hikaru",
    federation = "USA",
    standardRating = 2802,
    rapidRating = 2745,
    blitzRating = 2874,
    birthYear = "1987",
)

fun previewUiState() = EloUiState(
    selfQuery = "Carlsen Magnus",
    kFactor = "20",
    opponentQuery = "Nakamura Hikaru",
    playerLookupQuery = "Nakamura Hikaru",
    ratingType = RatingType.STANDARD,
    selectedSelf = previewPlayer(),
    profile = previewProfile(),
    searchResults = listOf(previewOpponent()),
    playerLookupResults = listOf(previewOpponent()),
    viewedPlayerProfile = previewViewedPlayerProfile(),
    selectedOpponents = listOf(
        SelectedOpponent(previewOpponent(), MatchResult.WIN),
    ),
    hasPersistedProfile = true,
    isRestoringProfile = false,
)

fun previewProfile() = FideProfile(
    player = previewPlayer(),
    fullName = "Carlsen, Magnus",
    federationName = "Norway",
    gender = "Male",
    fideTitle = "Grandmaster",
    worldChessProfileUrl = "https://worldchess.com",
    titleAwardedYear = "2004",
    ranks = PlayerRanks(
        world = RankBucket("1", "1"),
        nationalLabel = "National Rank NOR",
        national = RankBucket("1", "1"),
        continentLabel = "Continent Rank Europe",
        continent = RankBucket("1", "1"),
    ),
    stats = PlayerStats(
        totalGames = "3000",
        standardGames = "1200",
        rapidGames = "800",
        blitzGames = "1000",
    ),
    history = listOf(
        RatingHistoryEntry("2026-Apr", "2830", "0", "2819", "12", "2883", "24"),
        RatingHistoryEntry("2026-Mar", "2830", "9", "2815", "8", "2879", "17"),
    ),
)

fun previewViewedPlayerProfile() = FideProfile(
    player = previewOpponent(),
    fullName = "Nakamura, Hikaru",
    federationName = "United States",
    gender = "Male",
    fideTitle = "Grandmaster",
    worldChessProfileUrl = "https://worldchess.com",
    titleAwardedYear = "2003",
    ranks = PlayerRanks(
        world = RankBucket("2", "2"),
        nationalLabel = "National Rank USA",
        national = RankBucket("1", "1"),
        continentLabel = "Continent Rank America",
        continent = RankBucket("1", "1"),
    ),
    stats = PlayerStats(
        totalGames = "2800",
        standardGames = "1000",
        rapidGames = "900",
        blitzGames = "900",
    ),
    history = listOf(
        RatingHistoryEntry("2026-Apr", "2802", "5", "2745", "18", "2874", "32"),
        RatingHistoryEntry("2026-Mar", "2798", "7", "2740", "10", "2866", "25"),
    ),
)
