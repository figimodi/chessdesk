package com.filippogreco.elocalculator

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.AssistChip
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.FilterChip
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp

@Composable
fun ProfileScreen(
    uiState: EloUiState,
    onSelfQueryChange: (String) -> Unit,
    onSearchSelf: () -> Unit,
    onSelectSelf: (FidePlayer) -> Unit,
    contentPadding: PaddingValues,
) {
    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .padding(contentPadding),
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        item {
            Text("Profile", style = MaterialTheme.typography.headlineMedium)
        }

        item {
            ProfileHeaderCard(uiState.profile)
        }

        item {
            ProfileSwitcherCard(
                query = uiState.selfQuery,
                isLoading = uiState.isLoadingSelf || uiState.isLoadingProfile,
                errorMessage = uiState.selfErrorMessage ?: uiState.profileErrorMessage,
                results = uiState.selfSearchResults,
                ratingType = uiState.ratingType,
                onQueryChange = onSelfQueryChange,
                onSearch = onSearchSelf,
                onSelectProfile = onSelectSelf,
            )
        }

        item {
            RankingCard(uiState.profile)
        }

        item {
            TitleInfoCard(uiState.profile)
        }
    }
}

@Composable
fun PlayersScreen(
    uiState: EloUiState,
    onPlayerLookupQueryChange: (String) -> Unit,
    onSearchPlayerLookup: () -> Unit,
    onViewPlayerProfile: (FidePlayer) -> Unit,
    onViewedPlayerPageChange: (ViewedPlayerPage) -> Unit,
    onCloseViewedPlayer: () -> Unit,
    contentPadding: PaddingValues,
) {
    val viewedProfile = uiState.viewedPlayerProfile

    if (viewedProfile != null) {
        ViewedPlayerScreen(
            profile = viewedProfile,
            selectedPage = uiState.viewedPlayerPage,
            onPageChange = onViewedPlayerPageChange,
            onClose = onCloseViewedPlayer,
            contentPadding = contentPadding,
        )
        return
    }

    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .padding(contentPadding),
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        item {
            Text("Players", style = MaterialTheme.typography.headlineMedium)
        }

        item {
            SearchCard(
                query = uiState.playerLookupQuery,
                isLoading = uiState.isLoadingPlayerLookup || uiState.isLoadingViewedPlayerProfile,
                errorMessage = uiState.playerLookupErrorMessage,
                title = "Cerca un giocatore",
                label = "Nome giocatore",
                buttonText = "Cerca su FIDE",
                loadingText = "Cerco giocatore...",
                onQueryChange = onPlayerLookupQueryChange,
                onSearch = onSearchPlayerLookup,
            )
        }

        if (uiState.playerLookupResults.isNotEmpty()) {
            item {
                Text("Risultati", style = MaterialTheme.typography.titleLarge)
            }

            items(uiState.playerLookupResults, key = { it.id }) { player ->
                SearchResultCard(
                    player = player,
                    ratingType = uiState.ratingType,
                    buttonText = "Apri profilo",
                    onAdd = { onViewPlayerProfile(player) },
                )
            }
        }
    }
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun ViewedPlayerScreen(
    profile: FideProfile,
    selectedPage: ViewedPlayerPage,
    onPageChange: (ViewedPlayerPage) -> Unit,
    onClose: () -> Unit,
    contentPadding: PaddingValues,
) {
    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .padding(contentPadding),
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        item {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Button(onClick = onClose) {
                    Text("Back to search")
                }
                Text(profile.fullName, style = MaterialTheme.typography.headlineMedium)
                FlowRow(
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    ViewedPlayerPage.entries.forEach { page ->
                        FilterChip(
                            selected = selectedPage == page,
                            colors = darkSelectedChipColors(),
                            onClick = { onPageChange(page) },
                            label = { Text(page.label) },
                        )
                    }
                }
            }
        }

        when (selectedPage) {
            ViewedPlayerPage.PROFILE -> {
                item { ProfileHeaderCard(profile) }
                item { RankingCard(profile) }
                item { TitleInfoCard(profile) }
            }
            ViewedPlayerPage.STATS -> {
                item { StatsCard(profile) }
            }
            ViewedPlayerPage.HISTORY -> {
                if (profile.history.isEmpty()) {
                    item {
                        EmptyCard("Nessuno storico rating disponibile sul profilo FIDE.")
                    }
                } else {
                    items(profile.history, key = { it.period }) { entry ->
                        HistoryEntryCard(entry)
                    }
                }
            }
        }
    }
}

@Composable
fun HistoryScreen(profile: FideProfile?, contentPadding: PaddingValues) {
    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .padding(contentPadding),
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        item {
            Text("History", style = MaterialTheme.typography.headlineMedium)
        }

        val history = profile?.history.orEmpty()
        if (history.isEmpty()) {
            item {
                EmptyCard("Nessuno storico rating disponibile sul profilo FIDE.")
            }
        } else {
            items(history, key = { it.period }) { entry ->
                HistoryEntryCard(entry)
            }
        }
    }
}

@Composable
fun StatsScreen(profile: FideProfile?, contentPadding: PaddingValues) {
    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .padding(contentPadding),
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        item {
            Text("Stats", style = MaterialTheme.typography.headlineMedium)
        }

        item {
            StatsCard(profile)
        }
    }
}

@Composable
fun CalculatorScreen(
    uiState: EloUiState,
    onKFactorChange: (String) -> Unit,
    onRatingTypeChange: (RatingType) -> Unit,
    onOpponentQueryChange: (String) -> Unit,
    onSearchOpponents: () -> Unit,
    onAddOpponent: (FidePlayer) -> Unit,
    onResultChange: (String, MatchResult) -> Unit,
    onRemoveOpponent: (String) -> Unit,
    contentPadding: PaddingValues,
) {
    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .padding(contentPadding),
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        item {
            Text("Elo Calculator", style = MaterialTheme.typography.headlineMedium)
        }

        item {
            CalculatorSettingsCard(
                selectedSelf = uiState.selectedSelf,
                kFactor = uiState.kFactor,
                ratingType = uiState.ratingType,
                onKFactorChange = onKFactorChange,
                onRatingTypeChange = onRatingTypeChange,
            )
        }

        item {
            SearchCard(
                query = uiState.opponentQuery,
                isLoading = uiState.isLoading,
                errorMessage = uiState.errorMessage,
                title = "Cerca avversario",
                label = "Nome avversario",
                buttonText = "Cerca su FIDE",
                loadingText = "Cerco su FIDE...",
                onQueryChange = onOpponentQueryChange,
                onSearch = onSearchOpponents,
            )
        }

        if (uiState.searchResults.isNotEmpty()) {
            item {
                Text("Risultati FIDE", style = MaterialTheme.typography.titleLarge)
            }

            items(uiState.searchResults, key = { it.id }) { player ->
                SearchResultCard(
                    player = player,
                    ratingType = uiState.ratingType,
                    onAdd = { onAddOpponent(player) },
                )
            }
        }

        if (uiState.selectedOpponents.isNotEmpty()) {
            item {
                Text("Partite selezionate", style = MaterialTheme.typography.titleLarge)
            }

            item {
                SummaryCard(uiState)
            }

            items(uiState.selectedOpponents, key = { it.player.id }) { selected ->
                SelectedOpponentCard(
                    selected = selected,
                    ownRating = uiState.selectedSelf?.ratingFor(uiState.ratingType),
                    kFactor = uiState.kFactor.toIntOrNull(),
                    ratingType = uiState.ratingType,
                    onResultChange = { result -> onResultChange(selected.player.id, result) },
                    onRemove = { onRemoveOpponent(selected.player.id) },
                )
            }
        }
    }
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun SettingsCard(
    selfQuery: String,
    selectedSelf: FidePlayer?,
    kFactor: String,
    ratingType: RatingType,
    isLoadingSelf: Boolean,
    selfErrorMessage: String?,
    selfSearchResults: List<FidePlayer>,
    onKFactorChange: (String) -> Unit,
    onRatingTypeChange: (RatingType) -> Unit,
    onSelfQueryChange: (String) -> Unit,
    onSearchSelf: () -> Unit,
    onSelectSelf: (FidePlayer) -> Unit,
) {
    val selectedChipColors = darkSelectedChipColors()

    Card {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Text("Impostazioni", style = MaterialTheme.typography.titleMedium)
            SearchCard(
                query = selfQuery,
                isLoading = isLoadingSelf,
                errorMessage = selfErrorMessage,
                title = "Cerca te stesso",
                label = "Il tuo nome FIDE",
                buttonText = "Trova il mio profilo",
                loadingText = "Cerco il tuo profilo...",
                onQueryChange = onSelfQueryChange,
                onSearch = onSearchSelf,
            )
            selectedSelf?.let { player ->
                Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Text(
                        "Profilo selezionato: ${player.name}",
                        fontWeight = FontWeight.SemiBold,
                    )
                    RatingChips(player)
                    Text("Anno di nascita: ${player.birthYear.ifBlank { "n/d" }}")
                    Text("FIDE ID: ${player.id}")
                }
            }
            selfSearchResults.forEach { player ->
                SearchResultCard(
                    player = player,
                    ratingType = ratingType,
                    buttonText = "Usa questo profilo",
                    onAdd = { onSelectSelf(player) },
                )
            }
            OutlinedTextField(
                value = kFactor,
                onValueChange = onKFactorChange,
                label = { Text("K-factor") },
                modifier = Modifier.fillMaxWidth(),
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                singleLine = true,
            )
            FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                RatingType.entries.forEach { type ->
                    val isEnabled = selectedSelf?.ratingFor(type) != null || selectedSelf == null
                    FilterChip(
                        selected = type == ratingType,
                        enabled = isEnabled,
                        colors = selectedChipColors,
                        onClick = { onRatingTypeChange(type) },
                        label = { Text(type.label) },
                    )
                }
            }
        }
    }
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun CalculatorSettingsCard(
    selectedSelf: FidePlayer?,
    kFactor: String,
    ratingType: RatingType,
    onKFactorChange: (String) -> Unit,
    onRatingTypeChange: (RatingType) -> Unit,
) {
    val selectedChipColors = darkSelectedChipColors()

    Card {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Text("Impostazioni calcolo", style = MaterialTheme.typography.titleMedium)
            selectedSelf?.let { player ->
                Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Text("Profilo attivo: ${player.name}", fontWeight = FontWeight.SemiBold)
                    RatingChips(player)
                }
            }
            OutlinedTextField(
                value = kFactor,
                onValueChange = onKFactorChange,
                label = { Text("K-factor") },
                modifier = Modifier.fillMaxWidth(),
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                singleLine = true,
            )
            FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                RatingType.entries.forEach { type ->
                    val isEnabled = selectedSelf?.ratingFor(type) != null || selectedSelf == null
                    FilterChip(
                        selected = type == ratingType,
                        enabled = isEnabled,
                        colors = selectedChipColors,
                        onClick = { onRatingTypeChange(type) },
                        label = { Text(type.label) },
                    )
                }
            }
        }
    }
}

@Composable
fun SearchCard(
    query: String,
    isLoading: Boolean,
    errorMessage: String?,
    title: String,
    label: String,
    buttonText: String,
    loadingText: String,
    onQueryChange: (String) -> Unit,
    onSearch: () -> Unit,
) {
    Card {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Text(title, style = MaterialTheme.typography.titleMedium)
            OutlinedTextField(
                value = query,
                onValueChange = onQueryChange,
                label = { Text(label) },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
            )
            Button(onClick = onSearch, modifier = Modifier.fillMaxWidth(), enabled = !isLoading) {
                if (isLoading) {
                    CircularProgressIndicator(modifier = Modifier.padding(end = 8.dp))
                }
                Text(if (isLoading) loadingText else buttonText)
            }
            if (errorMessage != null) {
                Text(errorMessage, color = MaterialTheme.colorScheme.error)
            }
            Text(
                "Nota: nella ricerca FIDE usa il formato Cognome Nome.",
                style = MaterialTheme.typography.bodySmall,
            )
        }
    }
}

@Composable
fun SearchResultCard(
    player: FidePlayer,
    ratingType: RatingType,
    buttonText: String = "Aggiungi",
    onAdd: () -> Unit,
) {
    Card {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Text(player.name, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
            Text("Federazione: ${player.federation} • Nato: ${player.birthYear.ifBlank { "n/d" }}")
            RatingChips(player)
            Text(
                "Rating selezionato: ${player.ratingFor(ratingType)?.toString() ?: "non disponibile"}",
                style = MaterialTheme.typography.bodyMedium,
            )
            Button(onClick = onAdd, modifier = Modifier.fillMaxWidth()) {
                Text(buttonText)
            }
        }
    }
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun RatingChips(player: FidePlayer) {
    FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        AssistChip(onClick = {}, label = { Text("Std ${player.standardRating ?: "-"}") })
        AssistChip(onClick = {}, label = { Text("Rapid ${player.rapidRating ?: "-"}") })
        AssistChip(onClick = {}, label = { Text("Blitz ${player.blitzRating ?: "-"}") })
    }
}

@Composable
fun SummaryCard(uiState: EloUiState) {
    val ownRating = uiState.selectedSelf?.ratingFor(uiState.ratingType)
    val kFactor = uiState.kFactor.toIntOrNull()
    val total = uiState.selectedOpponents.sumOf { selected ->
        val opponentRating = selected.player.ratingFor(uiState.ratingType)
        val score = selected.result.score
        if (ownRating == null || kFactor == null || opponentRating == null || score == null) 0.0
        else calculateDelta(ownRating, opponentRating, kFactor, score)
    }

    Card {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Text("Totale partite giocate", style = MaterialTheme.typography.titleMedium)
            Text(
                "Variazione totale: ${formatDelta(total)}",
                style = MaterialTheme.typography.bodyLarge,
                fontWeight = FontWeight.SemiBold,
                color = deltaColor(total),
            )
            Text(
                "Il calcolo usa il rating del tuo profilo FIDE selezionato e la formula Elo classica con differenza limitata a 400 punti.",
                style = MaterialTheme.typography.bodySmall,
            )
        }
    }
}

@Composable
fun SelectedOpponentCard(
    selected: SelectedOpponent,
    ownRating: Int?,
    kFactor: Int?,
    ratingType: RatingType,
    onResultChange: (MatchResult) -> Unit,
    onRemove: () -> Unit,
) {
    val opponentRating = selected.player.ratingFor(ratingType)
    val delta = if (ownRating != null && kFactor != null && opponentRating != null) {
        EloDelta(
            win = calculateDelta(ownRating, opponentRating, kFactor, 1.0),
            draw = calculateDelta(ownRating, opponentRating, kFactor, 0.5),
            loss = calculateDelta(ownRating, opponentRating, kFactor, 0.0),
        )
    } else {
        null
    }

    Card {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Text(selected.player.name, style = MaterialTheme.typography.titleMedium)
                    Text("${selected.player.federation} • Rating ${opponentRating ?: "non disponibile"}")
                }
                Button(onClick = onRemove) {
                    Text("Rimuovi")
                }
            }

            ResultDropdown(selected.result, onResultChange)

            HorizontalDivider()

            if (delta == null) {
                Text("Seleziona il tuo profilo FIDE e scegli un avversario con rating disponibile.")
            } else {
                Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    Text("Se vinci: ${formatDelta(delta.win)}")
                    Text("Se fai patta: ${formatDelta(delta.draw)}")
                    Text("Se perdi: ${formatDelta(delta.loss)}")
                    selected.result.score?.let { score ->
                        Text(
                            "Risultato selezionato: ${formatDelta(calculateDelta(ownRating, opponentRating, kFactor, score))}",
                            fontWeight = FontWeight.SemiBold,
                        )
                    }
                }
            }
        }
    }
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun ResultDropdown(selected: MatchResult, onResultChange: (MatchResult) -> Unit) {
    val selectedChipColors = darkSelectedChipColors()

    Column {
        OutlinedTextField(
            value = selected.label,
            onValueChange = {},
            readOnly = true,
            label = { Text("Risultato") },
            modifier = Modifier.fillMaxWidth(),
        )
        FlowRow(
            horizontalArrangement = Arrangement.spacedBy(8.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            MatchResult.entries.forEach { result ->
                FilterChip(
                    selected = result == selected,
                    colors = selectedChipColors,
                    onClick = { onResultChange(result) },
                    label = { Text(result.label) },
                )
            }
        }
    }
}

@Composable
fun ProfileHeaderCard(profile: FideProfile?) {
    if (profile == null) {
        EmptyCard("Nessun profilo selezionato.")
        return
    }

    Card {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Text(profile.fullName, style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.SemiBold)
            Text("FIDE ID: ${profile.player.id}")
            Text("Federazione: ${profile.federationName}")
            Text("Titolo: ${profile.fideTitle}")
            Text("Genere: ${profile.gender}")
            Text("Anno di nascita: ${profile.player.birthYear}")
            RatingChips(profile.player)
        }
    }
}

@Composable
fun ProfileSwitcherCard(
    query: String,
    isLoading: Boolean,
    errorMessage: String?,
    results: List<FidePlayer>,
    ratingType: RatingType,
    onQueryChange: (String) -> Unit,
    onSearch: () -> Unit,
    onSelectProfile: (FidePlayer) -> Unit,
) {
    Card {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Text("Cambia profilo", style = MaterialTheme.typography.titleMedium)
            SearchCard(
                query = query,
                isLoading = isLoading,
                errorMessage = errorMessage,
                title = "Cerca un altro profilo",
                label = "Nome FIDE",
                buttonText = "Cerca su FIDE",
                loadingText = "Cerco profilo...",
                onQueryChange = onQueryChange,
                onSearch = onSearch,
            )
            results.forEach { player ->
                SearchResultCard(
                    player = player,
                    ratingType = ratingType,
                    buttonText = "Passa a questo profilo",
                    onAdd = { onSelectProfile(player) },
                )
            }
        }
    }
}

@Composable
fun RankingCard(profile: FideProfile?) {
    val ranks = profile?.ranks ?: run {
        EmptyCard("Rank non disponibili.")
        return
    }

    Card {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Text("Ranking", style = MaterialTheme.typography.titleMedium)
            RankBucketRow("World Rank", ranks.world)
            RankBucketRow(ranks.nationalLabel, ranks.national)
            RankBucketRow(ranks.continentLabel, ranks.continent)
        }
    }
}

@Composable
private fun RankBucketRow(label: String, bucket: RankBucket) {
    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
        Text(label, fontWeight = FontWeight.SemiBold)
        Text("Active players: ${bucket.activePlayers}")
        Text("All players: ${bucket.allPlayers}")
    }
}

@Composable
fun TitleInfoCard(profile: FideProfile?) {
    if (profile == null) {
        EmptyCard("Titoli non disponibili.")
        return
    }

    Card {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Text("Title", style = MaterialTheme.typography.titleMedium)
            Text(profile.fideTitle.ifBlank { "-" })
            profile.titleAwardedYear?.let {
                Text("Anno assegnazione: $it")
            }
            profile.worldChessProfileUrl?.let {
                Text("WorldChess: $it", style = MaterialTheme.typography.bodySmall)
            }
        }
    }
}

@Composable
fun StatsCard(profile: FideProfile?) {
    val stats = profile?.stats ?: run {
        EmptyCard("Statistiche non disponibili.")
        return
    }

    Card {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Text("Games", style = MaterialTheme.typography.titleMedium)
            Text("Total Games: ${stats.totalGames}")
            Text("Standard Games: ${stats.standardGames}")
            Text("Rapid Games: ${stats.rapidGames}")
            Text("Blitz Games: ${stats.blitzGames}")
        }
    }
}

@Composable
fun HistoryEntryCard(entry: RatingHistoryEntry) {
    Card {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(6.dp),
        ) {
            Text(entry.period, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
            Text("Standard: ${entry.standardRating} (${entry.standardGames} games)")
            Text("Rapid: ${entry.rapidRating} (${entry.rapidGames} games)")
            Text("Blitz: ${entry.blitzRating} (${entry.blitzGames} games)")
        }
    }
}

@Composable
fun EmptyCard(message: String) {
    Card {
        Text(
            text = message,
            modifier = Modifier.padding(16.dp),
            style = MaterialTheme.typography.bodyMedium,
        )
    }
}

@Preview(showBackground = true)
@Composable
private fun SettingsCardPreview() {
    MaterialTheme {
        SettingsCard(
            selfQuery = "Carlsen Magnus",
            selectedSelf = previewPlayer(),
            kFactor = "20",
            ratingType = RatingType.STANDARD,
            isLoadingSelf = false,
            selfErrorMessage = null,
            selfSearchResults = listOf(previewOpponent()),
            onKFactorChange = {},
            onRatingTypeChange = {},
            onSelfQueryChange = {},
            onSearchSelf = {},
            onSelectSelf = {},
        )
    }
}

@Preview(showBackground = true)
@Composable
private fun ProfileScreenPreview() {
    MaterialTheme {
        ProfileScreen(
            uiState = previewUiState(),
            onSelfQueryChange = {},
            onSearchSelf = {},
            onSelectSelf = {},
            contentPadding = PaddingValues(),
        )
    }
}

@Preview(showBackground = true)
@Composable
private fun PlayersScreenPreview() {
    MaterialTheme {
        PlayersScreen(
            uiState = previewUiState(),
            onPlayerLookupQueryChange = {},
            onSearchPlayerLookup = {},
            onViewPlayerProfile = {},
            onViewedPlayerPageChange = {},
            onCloseViewedPlayer = {},
            contentPadding = PaddingValues(),
        )
    }
}

@Preview(showBackground = true)
@Composable
private fun ViewedPlayerScreenPreview() {
    MaterialTheme {
        ViewedPlayerScreen(
            profile = previewViewedPlayerProfile(),
            selectedPage = ViewedPlayerPage.PROFILE,
            onPageChange = {},
            onClose = {},
            contentPadding = PaddingValues(),
        )
    }
}

@Preview(showBackground = true)
@Composable
private fun StatsScreenPreview() {
    MaterialTheme {
        StatsScreen(
            profile = previewProfile(),
            contentPadding = PaddingValues(),
        )
    }
}

@Preview(showBackground = true)
@Composable
private fun HistoryScreenPreview() {
    MaterialTheme {
        HistoryScreen(
            profile = previewProfile(),
            contentPadding = PaddingValues(),
        )
    }
}

@Preview(showBackground = true)
@Composable
private fun SelectedOpponentCardPreview() {
    MaterialTheme {
        SelectedOpponentCard(
            selected = SelectedOpponent(previewOpponent(), MatchResult.WIN),
            ownRating = 2400,
            kFactor = 20,
            ratingType = RatingType.STANDARD,
            onResultChange = {},
            onRemove = {},
        )
    }
}
