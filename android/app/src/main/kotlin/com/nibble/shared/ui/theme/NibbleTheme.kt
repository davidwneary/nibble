package com.nibble.shared.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.staticCompositionLocalOf

val LocalNibbleColors = staticCompositionLocalOf { lightColors() }

object NibbleTheme {
    val colors: NibbleColors
        @Composable get() = LocalNibbleColors.current
}

@Composable
fun NibbleTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit,
) {
    val colors = if (darkTheme) darkColors() else lightColors()

    CompositionLocalProvider(LocalNibbleColors provides colors) {
        content()
    }
}
