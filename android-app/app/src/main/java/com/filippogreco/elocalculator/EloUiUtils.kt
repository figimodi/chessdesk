package com.filippogreco.elocalculator

import androidx.compose.material3.FilterChipDefaults
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import kotlin.math.pow

fun calculateDelta(ownRating: Int, opponentRating: Int, kFactor: Int, actualScore: Double): Double {
    val boundedDifference = (opponentRating - ownRating).coerceIn(-400, 400)
    val expectedScore = 1.0 / (1.0 + 10.0.pow(boundedDifference / 400.0))
    return kFactor * (actualScore - expectedScore)
}

fun formatDelta(value: Double): String {
    val rounded = (value * 100.0).toInt() / 100.0
    return if (rounded >= 0) "+$rounded" else rounded.toString()
}

@Composable
fun deltaColor(value: Double) = when {
    value > 0.0 -> Color(0xFF2E7D32)
    value < 0.0 -> Color(0xFFC62828)
    else -> Color(0xFF757575)
}

@Composable
fun darkSelectedChipColors() = FilterChipDefaults.filterChipColors(
    selectedContainerColor = Color(0xFF1F2937),
    selectedLabelColor = Color.White,
)
