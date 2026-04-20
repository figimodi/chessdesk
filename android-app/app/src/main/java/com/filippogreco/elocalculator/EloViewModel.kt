package com.filippogreco.elocalculator

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

class EloViewModel(
    private val repository: FideRepository,
    private val profileStore: ProfileStore,
) : ViewModel() {
    private val _uiState = MutableStateFlow(EloUiState())
    val uiState: StateFlow<EloUiState> = _uiState

    init {
        restoreSelectedProfile()
    }

    private fun restoreSelectedProfile() {
        viewModelScope.launch {
            val savedProfileId = profileStore.loadSelectedProfileId()
            if (savedProfileId.isNullOrBlank()) {
                _uiState.update { it.copy(isRestoringProfile = false, hasPersistedProfile = false) }
                return@launch
            }

            _uiState.update { it.copy(hasPersistedProfile = true, isRestoringProfile = true) }
            loadProfile(savedProfileId, persist = false)
        }
    }

    fun updateSelfQuery(value: String) {
        _uiState.update { it.copy(selfQuery = value) }
    }

    fun updateKFactor(value: String) {
        _uiState.update { it.copy(kFactor = value.filterNumeric()) }
    }

    fun updateOpponentQuery(value: String) {
        _uiState.update { it.copy(opponentQuery = value) }
    }

    fun updatePlayerLookupQuery(value: String) {
        _uiState.update { it.copy(playerLookupQuery = value) }
    }

    fun updateRatingType(value: RatingType) {
        _uiState.update { state ->
            val selectedSelf = state.selectedSelf
            if (selectedSelf != null && selectedSelf.ratingFor(value) == null) state
            else state.copy(ratingType = value)
        }
    }

    fun updateCurrentPage(page: AppPage) {
        _uiState.update { it.copy(currentPage = page) }
    }

    fun updateViewedPlayerPage(page: ViewedPlayerPage) {
        _uiState.update { it.copy(viewedPlayerPage = page) }
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
        viewModelScope.launch {
            loadProfile(player.id, persist = true)
        }
    }

    private suspend fun loadProfile(profileId: String, persist: Boolean) {
        _uiState.update {
            it.copy(
                isLoadingProfile = true,
                isRestoringProfile = true,
                profileErrorMessage = null,
            )
        }

        val result = runCatching {
            repository.fetchProfile(profileId)
        }

        result.onSuccess { profile ->
            if (persist) profileStore.saveSelectedProfileId(profile.player.id)

            _uiState.update {
                val resolvedRatingType = when {
                    profile.player.ratingFor(it.ratingType) != null -> it.ratingType
                    else -> RatingType.entries.firstOrNull { type -> profile.player.ratingFor(type) != null } ?: it.ratingType
                }

                it.copy(
                    selectedSelf = profile.player,
                    profile = profile,
                    ratingType = resolvedRatingType,
                    selfQuery = "",
                    selfSearchResults = emptyList(),
                    selfErrorMessage = null,
                    hasPersistedProfile = true,
                    isRestoringProfile = false,
                    isLoadingProfile = false,
                    profileErrorMessage = null,
                    currentPage = AppPage.PROFILE,
                )
            }
        }.onFailure {
            _uiState.update {
                it.copy(
                    isLoadingProfile = false,
                    isRestoringProfile = false,
                    hasPersistedProfile = false,
                    profileErrorMessage = "Impossibile caricare il profilo FIDE. Riprova.",
                )
            }
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

    fun searchPlayerLookup() {
        val query = uiState.value.playerLookupQuery.trim()
        if (query.isBlank()) {
            _uiState.update { it.copy(playerLookupErrorMessage = "Inserisci il nome del giocatore.") }
            return
        }

        viewModelScope.launch {
            _uiState.update {
                it.copy(
                    isLoadingPlayerLookup = true,
                    playerLookupErrorMessage = null,
                    playerLookupResults = emptyList(),
                )
            }

            val result = runCatching {
                repository.searchPlayers(query, uiState.value.ratingType)
            }

            result.onSuccess { players ->
                _uiState.update {
                    it.copy(
                        isLoadingPlayerLookup = false,
                        playerLookupResults = players,
                        playerLookupErrorMessage = if (players.isEmpty()) "Nessun giocatore trovato." else null,
                    )
                }
            }.onFailure {
                _uiState.update {
                    it.copy(
                        isLoadingPlayerLookup = false,
                        playerLookupErrorMessage = "Ricerca FIDE non riuscita. Riprova tra poco.",
                    )
                }
            }
        }
    }

    fun viewPlayerProfile(player: FidePlayer) {
        viewModelScope.launch {
            _uiState.update {
                it.copy(
                    isLoadingViewedPlayerProfile = true,
                    playerLookupErrorMessage = null,
                )
            }

            val result = runCatching {
                repository.fetchProfile(player.id)
            }

            result.onSuccess { profile ->
                _uiState.update {
                    it.copy(
                        isLoadingViewedPlayerProfile = false,
                        viewedPlayerProfile = profile,
                        viewedPlayerPage = ViewedPlayerPage.PROFILE,
                        currentPage = AppPage.PLAYERS,
                    )
                }
            }.onFailure {
                _uiState.update {
                    it.copy(
                        isLoadingViewedPlayerProfile = false,
                        playerLookupErrorMessage = "Impossibile caricare il profilo del giocatore.",
                    )
                }
            }
        }
    }

    fun clearViewedPlayerProfile() {
        _uiState.update {
            it.copy(
                viewedPlayerProfile = null,
                viewedPlayerPage = ViewedPlayerPage.PROFILE,
                playerLookupErrorMessage = null,
            )
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
        fun factory(repository: FideRepository, profileStore: ProfileStore): ViewModelProvider.Factory =
            object : ViewModelProvider.Factory {
                @Suppress("UNCHECKED_CAST")
                override fun <T : ViewModel> create(modelClass: Class<T>): T {
                    return EloViewModel(repository, profileStore) as T
                }
            }
    }
}

private fun String.filterNumeric(): String = filter { it.isDigit() }
