package com.filippogreco.elocalculator

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle

@Composable
fun EloCalculatorRoute(viewModel: EloViewModel) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()

    ChessDeskApp(
        uiState = uiState,
        onKFactorChange = viewModel::updateKFactor,
        onRatingTypeChange = viewModel::updateRatingType,
        onSelfQueryChange = viewModel::updateSelfQuery,
        onSearchSelf = viewModel::searchSelf,
        onSelectSelf = viewModel::selectSelf,
        onPageChange = viewModel::updateCurrentPage,
        onOpponentQueryChange = viewModel::updateOpponentQuery,
        onSearchOpponents = viewModel::searchOpponents,
        onPlayerLookupQueryChange = viewModel::updatePlayerLookupQuery,
        onSearchPlayerLookup = viewModel::searchPlayerLookup,
        onViewPlayerProfile = viewModel::viewPlayerProfile,
        onViewedPlayerPageChange = viewModel::updateViewedPlayerPage,
        onCloseViewedPlayer = viewModel::clearViewedPlayerProfile,
        onAddOpponent = viewModel::addOpponent,
        onResultChange = viewModel::updateResult,
        onRemoveOpponent = viewModel::removeOpponent,
    )
}

@Composable
fun ChessDeskApp(
    uiState: EloUiState,
    onKFactorChange: (String) -> Unit,
    onRatingTypeChange: (RatingType) -> Unit,
    onSelfQueryChange: (String) -> Unit,
    onSearchSelf: () -> Unit,
    onSelectSelf: (FidePlayer) -> Unit,
    onPageChange: (AppPage) -> Unit,
    onOpponentQueryChange: (String) -> Unit,
    onSearchOpponents: () -> Unit,
    onPlayerLookupQueryChange: (String) -> Unit,
    onSearchPlayerLookup: () -> Unit,
    onViewPlayerProfile: (FidePlayer) -> Unit,
    onViewedPlayerPageChange: (ViewedPlayerPage) -> Unit,
    onCloseViewedPlayer: () -> Unit,
    onAddOpponent: (FidePlayer) -> Unit,
    onResultChange: (String, MatchResult) -> Unit,
    onRemoveOpponent: (String) -> Unit,
) {
    if (uiState.isRestoringProfile && uiState.profile == null) {
        FullScreenLoading("Carico il profilo FIDE...")
        return
    }

    if (uiState.profile == null) {
        ProfileSelectionScreen(
            query = uiState.selfQuery,
            isLoading = uiState.isLoadingSelf || uiState.isLoadingProfile,
            errorMessage = uiState.selfErrorMessage ?: uiState.profileErrorMessage,
            results = uiState.selfSearchResults,
            ratingType = uiState.ratingType,
            onQueryChange = onSelfQueryChange,
            onSearch = onSearchSelf,
            onSelectProfile = onSelectSelf,
        )
        return
    }

    Scaffold(
        bottomBar = {
            NavigationBar {
                AppPage.entries.forEach { page ->
                    NavigationBarItem(
                        selected = uiState.currentPage == page,
                        onClick = { onPageChange(page) },
                        icon = {},
                        label = { Text(page.label) },
                    )
                }
            }
        }
    ) { padding ->
        when (uiState.currentPage) {
            AppPage.PROFILE -> ProfileScreen(
                uiState = uiState,
                onSelfQueryChange = onSelfQueryChange,
                onSearchSelf = onSearchSelf,
                onSelectSelf = onSelectSelf,
                contentPadding = padding,
            )
            AppPage.PLAYERS -> PlayersScreen(
                uiState = uiState,
                onPlayerLookupQueryChange = onPlayerLookupQueryChange,
                onSearchPlayerLookup = onSearchPlayerLookup,
                onViewPlayerProfile = onViewPlayerProfile,
                onViewedPlayerPageChange = onViewedPlayerPageChange,
                onCloseViewedPlayer = onCloseViewedPlayer,
                contentPadding = padding,
            )
            AppPage.HISTORY -> HistoryScreen(uiState.profile, padding)
            AppPage.STATS -> StatsScreen(uiState.profile, padding)
            AppPage.CALCULATOR -> CalculatorScreen(
                uiState = uiState,
                onKFactorChange = onKFactorChange,
                onRatingTypeChange = onRatingTypeChange,
                onOpponentQueryChange = onOpponentQueryChange,
                onSearchOpponents = onSearchOpponents,
                onAddOpponent = onAddOpponent,
                onResultChange = onResultChange,
                onRemoveOpponent = onRemoveOpponent,
                contentPadding = padding,
            )
        }
    }
}

@Composable
private fun FullScreenLoading(message: String) {
    Scaffold { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(24.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            CircularProgressIndicator()
            Text(message, style = MaterialTheme.typography.titleMedium)
        }
    }
}

@Composable
private fun ProfileSelectionScreen(
    query: String,
    isLoading: Boolean,
    errorMessage: String?,
    results: List<FidePlayer>,
    ratingType: RatingType,
    onQueryChange: (String) -> Unit,
    onSearch: () -> Unit,
    onSelectProfile: (FidePlayer) -> Unit,
) {
    Scaffold { padding ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding),
            contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            item {
                Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    Text("ChessDesk", style = MaterialTheme.typography.headlineMedium)
                    Text(
                        "Cerca il tuo profilo FIDE per iniziare. Dopo la prima selezione resterai dentro al tuo profilo e potrai cambiarlo dalla pagina Profile.",
                        style = MaterialTheme.typography.bodyMedium,
                    )
                }
            }

            item {
                SearchCard(
                    query = query,
                    isLoading = isLoading,
                    errorMessage = errorMessage,
                    title = "Trova il tuo profilo",
                    label = "Nome FIDE",
                    buttonText = "Cerca su FIDE",
                    loadingText = "Cerco il tuo profilo...",
                    onQueryChange = onQueryChange,
                    onSearch = onSearch,
                )
            }

            if (results.isNotEmpty()) {
                item {
                    Text("Profili trovati", style = MaterialTheme.typography.titleLarge)
                }

                items(
                    items = results,
                    key = { player -> player.id },
                ) { player ->
                    SearchResultCard(
                        player = player,
                        ratingType = ratingType,
                        buttonText = "Usa questo profilo",
                        onAdd = { onSelectProfile(player) },
                    )
                }
            }
        }
    }
}

@Preview(showBackground = true)
@Composable
private fun ChessDeskAppPreview() {
    MaterialTheme {
        ChessDeskApp(
            uiState = previewUiState(),
            onKFactorChange = {},
            onRatingTypeChange = {},
            onSelfQueryChange = {},
            onSearchSelf = {},
            onSelectSelf = {},
            onPageChange = {},
            onOpponentQueryChange = {},
            onSearchOpponents = {},
            onPlayerLookupQueryChange = {},
            onSearchPlayerLookup = {},
            onViewPlayerProfile = {},
            onViewedPlayerPageChange = {},
            onCloseViewedPlayer = {},
            onAddOpponent = {},
            onResultChange = { _, _ -> },
            onRemoveOpponent = {},
        )
    }
}
