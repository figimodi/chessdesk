package com.filippogreco.elocalculator

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request
import org.jsoup.Jsoup
import java.net.URLEncoder

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

    suspend fun fetchProfile(playerId: String): FideProfile = withContext(Dispatchers.IO) {
        val request = Request.Builder()
            .url("https://ratings.fide.com/profile/$playerId")
            .header("User-Agent", "Mozilla/5.0")
            .build()

        client.newCall(request).execute().use { response ->
            if (!response.isSuccessful) error("FIDE profile request failed: ${response.code}")
            val body = response.body?.string().orEmpty()
            parseProfile(body, playerId)
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

    private fun parseProfile(html: String, playerId: String): FideProfile {
        val doc = Jsoup.parse(html)
        val textBlocks = doc.select("div, td, span, p, h1, h2, h3, h4, h5, h6, a")
            .map { it.text().trim() }
            .filter { it.isNotBlank() }

        val name = doc.select("h1, h2, h3").map { it.text().trim() }
            .firstOrNull { it.contains(",") && !it.contains("FIDE Profile", ignoreCase = true) }
            ?: extractMetaTitle(doc).substringBefore(" FIDE Profile")

        val standardRating = extractRating(html, "STANDARD")
        val rapidRating = extractRating(html, "RAPID")
        val blitzRating = extractRating(html, "BLITZ")

        val federationValue = extractValueAfterLabel(textBlocks, listOf("Federation"))
        val federationName = federationValue.substringBefore("(").ifBlank { federationValue }
        val birthYear = extractValueAfterLabel(textBlocks, listOf("B-Year", "Birth Year"))
        val gender = extractValueAfterLabel(textBlocks, listOf("Gender"))
        val fideTitle = extractValueAfterLabel(textBlocks, listOf("FIDE title"))
        val titleAwardedYear = extractTitleYear(textBlocks)
        val worldChessProfileUrl = doc.select("a[href*=worldchess]").firstOrNull()?.attr("href")

        val player = FidePlayer(
            id = extractValueAfterLabel(textBlocks, listOf("FIDE ID")).ifBlank { playerId },
            name = name,
            federation = federationName.takeLast(3).takeIf { it.length == 3 } ?: federationName,
            standardRating = standardRating,
            rapidRating = rapidRating,
            blitzRating = blitzRating,
            birthYear = birthYear,
        )

        return FideProfile(
            player = player,
            fullName = name,
            federationName = federationName,
            gender = gender,
            fideTitle = fideTitle,
            worldChessProfileUrl = worldChessProfileUrl,
            titleAwardedYear = titleAwardedYear,
            ranks = PlayerRanks(
                world = RankBucket(
                    activePlayers = extractRankValue(textBlocks, "World Rank", "Active players"),
                    allPlayers = extractRankValue(textBlocks, "World Rank", "All players"),
                ),
                nationalLabel = extractRankHeading(textBlocks, "National Rank") ?: "National Rank",
                national = RankBucket(
                    activePlayers = extractRankValue(textBlocks, "National Rank", "Active players"),
                    allPlayers = extractRankValue(textBlocks, "National Rank", "All players"),
                ),
                continentLabel = extractRankHeading(textBlocks, "Continent Rank") ?: "Continent Rank",
                continent = RankBucket(
                    activePlayers = extractRankValue(textBlocks, "Continent Rank", "Active players"),
                    allPlayers = extractRankValue(textBlocks, "Continent Rank", "All players"),
                ),
            ),
            stats = PlayerStats(
                totalGames = extractValueAfterLabel(textBlocks, listOf("Total Games")),
                standardGames = extractValueAfterLabel(textBlocks, listOf("Standard Games")),
                rapidGames = extractValueAfterLabel(textBlocks, listOf("Rapid Games")),
                blitzGames = extractValueAfterLabel(textBlocks, listOf("Blitz Games")),
            ),
            history = extractHistory(textBlocks),
        )
    }

    private fun extractMetaTitle(doc: org.jsoup.nodes.Document): String =
        doc.title().ifBlank { "FIDE Player" }

    private fun extractRating(html: String, label: String): Int? {
        val regex = Regex("""(?:logo_(?:std|rpd|blitz)\\.svg.*?|>)\\s*(\\d{3,4})\\s*<[^>]*>\\s*$label""", RegexOption.IGNORE_CASE)
        return regex.find(html)?.groupValues?.getOrNull(1)?.toIntOrNull()
    }

    private fun extractValueAfterLabel(textBlocks: List<String>, labels: List<String>): String {
        val index = textBlocks.indexOfFirst { block -> labels.any { it.equals(block, ignoreCase = true) } }
        return if (index >= 0 && index + 1 < textBlocks.size) textBlocks[index + 1] else "-"
    }

    private fun extractRankHeading(textBlocks: List<String>, prefix: String): String? =
        textBlocks.firstOrNull { it.startsWith(prefix, ignoreCase = true) }

    private fun extractRankValue(textBlocks: List<String>, headingPrefix: String, label: String): String {
        val headingIndex = textBlocks.indexOfFirst { it.startsWith(headingPrefix, ignoreCase = true) }
        if (headingIndex == -1) return "-"
        val localWindow = textBlocks.drop(headingIndex).take(8)
        val labelIndex = localWindow.indexOfFirst { it.equals(label, ignoreCase = true) }
        return if (labelIndex >= 0 && labelIndex + 1 < localWindow.size) localWindow[labelIndex + 1] else "-"
    }

    private fun extractTitleYear(textBlocks: List<String>): String? {
        val titlesIndex = textBlocks.indexOfFirst { it.equals("Titles", ignoreCase = true) }
        if (titlesIndex == -1) return null
        return textBlocks.drop(titlesIndex).firstOrNull { it.matches(Regex("\\d{4}")) }
    }

    private fun extractHistory(textBlocks: List<String>): List<RatingHistoryEntry> {
        val entries = mutableListOf<RatingHistoryEntry>()
        val periodRegex = Regex("\\d{4}-[A-Za-z]{3}")
        var index = textBlocks.indexOfFirst { it.equals("Period", ignoreCase = true) }
        if (index == -1) return emptyList()
        index += 1

        while (index + 6 < textBlocks.size) {
            val period = textBlocks[index]
            if (!period.matches(periodRegex)) {
                index += 1
                continue
            }
            entries += RatingHistoryEntry(
                period = period,
                standardRating = textBlocks[index + 1],
                standardGames = textBlocks[index + 2],
                rapidRating = textBlocks[index + 3],
                rapidGames = textBlocks[index + 4],
                blitzRating = textBlocks[index + 5],
                blitzGames = textBlocks[index + 6],
            )
            index += 7
        }

        return entries
    }
}
