package com.nibble.app

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Test

class MainActivityTest {

    @Test
    fun `app name constant is Nibble`() {
        assertEquals("Nibble", AppConstants.APP_NAME)
    }

    @Test
    fun `app tagline is defined`() {
        assertNotNull(AppConstants.APP_TAGLINE)
        assertEquals("Your personal recipe collection", AppConstants.APP_TAGLINE)
    }
}
