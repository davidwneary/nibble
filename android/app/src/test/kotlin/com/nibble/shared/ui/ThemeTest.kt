package com.nibble.shared.ui

import com.nibble.shared.ui.theme.NibbleColors
import com.nibble.shared.ui.theme.lightColors
import com.nibble.shared.ui.theme.darkColors
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotEquals
import org.junit.Test

class ThemeTest {

    @Test
    fun `light theme has correct background color`() {
        val colors = lightColors()
        assertEquals(0xFFFAFAFA, colors.background.value)
    }

    @Test
    fun `dark theme has correct background color`() {
        val colors = darkColors()
        assertEquals(0xFF1C1C1E, colors.background.value)
    }

    @Test
    fun `light and dark themes have different backgrounds`() {
        val light = lightColors()
        val dark = darkColors()
        assertNotEquals(light.background, dark.background)
    }

    @Test
    fun `primary color is warm orange`() {
        val colors = lightColors()
        assertEquals(0xFFFF6B35, colors.primary.value)
    }
}
