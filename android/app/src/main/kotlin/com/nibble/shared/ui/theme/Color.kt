package com.nibble.shared.ui.theme

import androidx.compose.ui.graphics.Color

data class NibbleColors(
    val background: Color,
    val surface: Color,
    val surfaceHover: Color,
    val primary: Color,
    val primaryHover: Color,
    val textPrimary: Color,
    val textSecondary: Color,
    val textTertiary: Color,
    val divider: Color,
    val success: Color,
    val error: Color,
    val warning: Color,
)

fun lightColors() = NibbleColors(
    background = Color(0xFFFAFAFA),
    surface = Color(0xFFFFFFFF),
    surfaceHover = Color(0xFFF5F5F5),
    primary = Color(0xFFFF6B35),
    primaryHover = Color(0xFFE85A2A),
    textPrimary = Color(0xFF1A1A1A),
    textSecondary = Color(0xFF6D6D72),
    textTertiary = Color(0xFFAEAEB2),
    divider = Color(0xFFEAEAEB),
    success = Color(0xFF34C759),
    error = Color(0xFFFF3B30),
    warning = Color(0xFFFF9500),
)

fun darkColors() = NibbleColors(
    background = Color(0xFF1C1C1E),
    surface = Color(0xFF2C2C2E),
    surfaceHover = Color(0xFF3A3A3C),
    primary = Color(0xFFFF8F5E),
    primaryHover = Color(0xFFFFA070),
    textPrimary = Color(0xFFF5F5F5),
    textSecondary = Color(0xFF8E8E93),
    textTertiary = Color(0xFF636366),
    divider = Color(0xFF38383A),
    success = Color(0xFF30D158),
    error = Color(0xFFFF453A),
    warning = Color(0xFFFFD60A),
)
