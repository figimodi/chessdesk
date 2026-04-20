package com.filippogreco.elocalculator

import android.content.Context

class ProfileStore(context: Context) {
    private val preferences = context.getSharedPreferences("profile_store", Context.MODE_PRIVATE)

    fun saveSelectedProfileId(profileId: String) {
        preferences.edit().putString(KEY_SELECTED_PROFILE_ID, profileId).apply()
    }

    fun loadSelectedProfileId(): String? = preferences.getString(KEY_SELECTED_PROFILE_ID, null)

    companion object {
        private const val KEY_SELECTED_PROFILE_ID = "selected_profile_id"
    }
}
