package com.filippogreco.elocalculator

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
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
import androidx.compose.material3.FilterChipDefaults
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request
import org.jsoup.Jsoup
import java.net.URLEncoder
import kotlin.math.pow

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme {
                Surface(modifier = Modifier.fillMaxSize()) {
                    val viewModel: EloViewModel = viewModel(
                        factory = EloViewModel.factory(FideRepository())
                    )
                    EloCalculatorScreen(viewModel)
                }
            }
        }
    }
}

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

data class EloUiState(
    val selfQuery: String = "",
    val kFactor: String = "20",
    val opponentQuery: String = "",
    val ratingType: RatingType = RatingType.STANDARD,
    val isLoading: Boolean = false,
    val isLoadingSelf: Boolean = false,
    val errorMessage: String? = null,
    val selfErrorMessage: String? = null,
    val selfSearchResults: List<FidePlayer> = emptyList(),
    val selectedSelf: FidePlayer? = null,
    val searchResults: List<FidePlayer> = emptyList(),
    val selectedOpponents: List<SelectedOpponent> = emptyList(),
)

class EloViewModel(
    private val repository: FideRepository,
) : ViewModel() {
    private val _uiState = MutableStateFlow(EloUiState())
    val uiState: StateFlow<EloUiState> = _uiState

    fun updateSelfQuery(value: String) {
        _uiState.update { it.copy(selfQuery = value) }
    }

    fun updateKFactor(value: String) {
        _uiState.update { it.copy(kFactor = value.filterNumeric()) }
    }

    fun updateOpponentQuery(value: String) {
        _uiState.update { it.copy(opponentQuery = value) }
    }

    fun updateRatingType(value: RatingType) {
        _uiState.update { state ->
            val selectedSelf = state.selectedSelf
            if (selectedSelf != null && selectedSelf.ratingFor(value) == null) state
            else state.copy(ratingType = value)
        }
    }

    fun searchSelf() {
        val query = uiState.value.selfQuery.trim()
        if (query.isBlank()) {
            _uiState.update { it.copy(selfErrorMessage = "Inserisci il tuo nome FIDE.") }
            return
        }

        viewModelScope.launch {
            _uiState.update {
                it.copy(isLoadingSelf = true, selfErrorMessage = null, selfSearchResults = emptyList())
            }

            val result = runCatching {
                repository.searchPlayers(query, uiState.value.ratingType)
            }

            result.onSuccess { players ->
                _uiState.update {
                    it.copy(
                        isLoadingSelf = false,
                        selfSearchResults = players,
                        selfErrorMessage = if (players.isEmpty()) "Nessun giocatore trovato." else null,
                    )
                }
            }.onFailure {
                _uiState.update {
                    it.copy(
                        isLoadingSelf = false,
                        selfErrorMessage = "Ricerca FIDE non riuscita. Riprova tra poco.",
                    )
                }
            }
        }
    }

    fun selectSelf(player: FidePlayer) {
        _uiState.update {
            val resolvedRatingType = when {
                player.ratingFor(it.ratingType) != null -> it.ratingType
                else -> RatingType.entries.firstOrNull { type -> player.ratingFor(type) != null } ?: it.ratingType
            }

            it.copy(
                selectedSelf = player,
                ratingType = resolvedRatingType,
                selfQuery = "",
                selfSearchResults = emptyList(),
                selfErrorMessage = null,
            )
        }
    }

    fun searchOpponents() {
        val query = uiState.value.opponentQuery.trim()
        if (query.isBlank()) {
            _uiState.update { it.copy(errorMessage = "Inserisci il nome dell'avversario.") }
            return
        }

        viewModelScope.launch {
            _uiState.update {
                it.copy(isLoading = true, errorMessage = null, searchResults = emptyList())
            }

            val result = runCatching {
                repository.searchPlayers(query, uiState.value.ratingType)
            }

            result.onSuccess { players ->
                _uiState.update {
                    it.copy(
                        isLoading = false,
                        searchResults = players,
                        errorMessage = if (players.isEmpty()) "Nessun giocatore trovato." else null,
                    )
                }
            }.onFailure {
                _uiState.update {
                    it.copy(
                        isLoading = false,
                        errorMessage = "Ricerca FIDE non riuscita. Riprova tra poco.",
                    )
                }
            }
        }
    }

    fun addOpponent(player: FidePlayer) {
        _uiState.update { state ->
            val alreadySelected = state.selectedOpponents.any { it.player.id == player.id }
            if (alreadySelected) state
            else state.copy(
                opponentQuery = "",
                selectedOpponents = state.selectedOpponents + SelectedOpponent(player),
                searchResults = emptyList(),
            )
        }
    }

    fun updateResult(playerId: String, result: MatchResult) {
        _uiState.update { state ->
            state.copy(
                selectedOpponents = state.selectedOpponents.map {
                    if (it.player.id == playerId) it.copy(result = result) else it
                }
            )
        }
    }

    fun removeOpponent(playerId: String) {
        _uiState.update { state ->
            state.copy(selectedOpponents = state.selectedOpponents.filterNot { it.player.id == playerId })
        }
    }

    companion object {
        fun factory(repository: FideRepository): ViewModelProvider.Factory =
            object : ViewModelProvider.Factory {
                @Suppress("UNCHECKED_CAST")
                override fun <T : ViewModel> create(modelClass: Class<T>): T {
                    return EloViewModel(repository) as T
                }
            }
    }
}

class FideRepository {
    private val client = OkHttpClient.Builder().build()

    suspend fun searchPlayers(query: String, ratingType: RatingType): List<FidePlayer> = withContext(Dispatchers.IO) {
        val normalizedQuery = query.trim()
        val request = Request.Builder()
            .url("https://ratings.fide.com/incl_search_l.php?search=${URLEncoder.encode(normalizedQuery, Charsets.UTF_8.name())}&simple=1")
            .header("User-Agent", "Mozilla/5.0")
            .header("X-Requested-With", "XMLHttpRequest")
            .build()

        client.newCall(request).execute().use { response ->
            if (!response.isSuccessful) error("FIDE request failed: ${response.code}")
            val body = response.body?.string().orEmpty()
            parsePlayers(body, normalizedQuery, ratingType)
        }
    }

    private fun parsePlayers(html: String, query: String, ratingType: RatingType): List<FidePlayer> {
        val doc = Jsoup.parse(html)
        val requiredTerm = query.substringBefore(" ").trim()

        // The search endpoint returns an HTML fragment with one result table.
        return doc.select("table#table_results tbody tr")
            .mapNotNull { row ->
                val cells = row.select("td")
                if (cells.size < 9) return@mapNotNull null

                FidePlayer(
                    id = cells[0].text().trim(),
                    name = cells[1].selectFirst("a.found_name")?.text()?.trim().orEmpty(),
                    federation = cells[4].text().trim(),
                    standardRating = cells[5].text().trim().toIntOrNull(),
                    rapidRating = cells[6].text().trim().toIntOrNull(),
                    blitzRating = cells[7].text().trim().toIntOrNull(),
                    birthYear = cells[8].text().trim(),
                )
            }
            .filter { player ->
                requiredTerm.isBlank() || player.name.contains(requiredTerm, ignoreCase = true)
            }
            .let { sortPlayers(it, query, ratingType) }
    }

    private fun sortPlayers(players: List<FidePlayer>, query: String, ratingType: RatingType): List<FidePlayer> {
        return players.sortedWith(
            compareBy<FidePlayer> {
                when {
                    it.name.equals(query, ignoreCase = true) -> 0
                    it.name.startsWith(query, ignoreCase = true) -> 1
                    it.name.contains(query, ignoreCase = true) -> 2
                    else -> 3
                }
            }.thenByDescending { it.ratingFor(ratingType) ?: -1 }
        )
    }
}

@Composable
private fun EloCalculatorScreen(viewModel: EloViewModel) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()

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
                    Text("Calcolatore Elo FIDE", style = MaterialTheme.typography.headlineMedium)
                }
            }

            item {
                SettingsCard(
                    selfQuery = uiState.selfQuery,
                    selectedSelf = uiState.selectedSelf,
                    kFactor = uiState.kFactor,
                    ratingType = uiState.ratingType,
                    isLoadingSelf = uiState.isLoadingSelf,
                    selfErrorMessage = uiState.selfErrorMessage,
                    selfSearchResults = uiState.selfSearchResults,
                    onKFactorChange = viewModel::updateKFactor,
                    onRatingTypeChange = viewModel::updateRatingType,
                    onSelfQueryChange = viewModel::updateSelfQuery,
                    onSearchSelf = viewModel::searchSelf,
                    onSelectSelf = viewModel::selectSelf,
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
                    onQueryChange = viewModel::updateOpponentQuery,
                    onSearch = viewModel::searchOpponents,
                )
            }

            if (uiState.searchResults.isNotEmpty()) {
                item {
                    Text("Risultati FIDE", style = MaterialTheme.typography.titleLarge)
                }

                items(
                    items = uiState.searchResults,
                    key = { player -> player.id },
                ) { player ->
                    SearchResultCard(
                        player = player,
                        ratingType = uiState.ratingType,
                        onAdd = { viewModel.addOpponent(player) },
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

                items(
                    items = uiState.selectedOpponents,
                    key = { selected -> selected.player.id },
                ) { selected ->
                    SelectedOpponentCard(
                        selected = selected,
                        ownRating = uiState.selectedSelf?.ratingFor(uiState.ratingType),
                        kFactor = uiState.kFactor.toIntOrNull(),
                        ratingType = uiState.ratingType,
                        onResultChange = { result -> viewModel.updateResult(selected.player.id, result) },
                        onRemove = { viewModel.removeOpponent(selected.player.id) },
                    )
                }
            }
        }
    }
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
private fun SettingsCard(
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

@Composable
private fun SearchCard(
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
private fun SearchResultCard(
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
private fun RatingChips(player: FidePlayer) {
    FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        AssistChip(onClick = {}, label = { Text("Std ${player.standardRating ?: "-"}") })
        AssistChip(onClick = {}, label = { Text("Rapid ${player.rapidRating ?: "-"}") })
        AssistChip(onClick = {}, label = { Text("Blitz ${player.blitzRating ?: "-"}") })
    }
}

@Composable
private fun SummaryCard(uiState: EloUiState) {
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
private fun SelectedOpponentCard(
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
    val resolvedOwnRating = ownRating
    val resolvedOpponentRating = opponentRating
    val resolvedKFactor = kFactor

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
                    if (resolvedOwnRating != null && resolvedOpponentRating != null && resolvedKFactor != null) {
                        selected.result.score?.let { score ->
                        Text(
                            "Risultato selezionato: ${formatDelta(calculateDelta(resolvedOwnRating, resolvedOpponentRating, resolvedKFactor, score))}",
                            fontWeight = FontWeight.SemiBold,
                        )
                    }
                    }
                }
            }
        }
    }
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
private fun ResultDropdown(selected: MatchResult, onResultChange: (MatchResult) -> Unit) {
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
                    onClick = {
                        onResultChange(result)
                    },
                    label = { Text(result.label) },
                )
            }
        }
    }
}

private fun calculateDelta(ownRating: Int, opponentRating: Int, kFactor: Int, actualScore: Double): Double {
    val boundedDifference = (opponentRating - ownRating).coerceIn(-400, 400)
    val expectedScore = 1.0 / (1.0 + 10.0.pow(boundedDifference / 400.0))
    return kFactor * (actualScore - expectedScore)
}

private fun formatDelta(value: Double): String {
    val rounded = (value * 100.0).toInt() / 100.0
    return if (rounded >= 0) "+$rounded" else rounded.toString()
}

@Composable
private fun deltaColor(value: Double) = when {
    value > 0.0 -> Color(0xFF2E7D32)
    value < 0.0 -> Color(0xFFC62828)
    else -> Color(0xFF757575)
}

@Composable
private fun darkSelectedChipColors() = FilterChipDefaults.filterChipColors(
    selectedContainerColor = Color(0xFF1F2937),
    selectedLabelColor = Color.White,
)

private fun String.filterNumeric(): String = filter { it.isDigit() }
