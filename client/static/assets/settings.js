/*
 * Settings and account management code for static HabitHub client.
 *
 * AI use and code origin:
 * - AI used: GitHub Copilot with GPT-5.4.
 * 
 * - Prompt summary used for AI-assisted parts:
 *   "Create client-side settings page logic for profile updates and account
 *   deletion in a static frontend that talks to a REST API."
 * 
 * - AI-assisted methods in this file: deleteAccountTree and initSettings.
 * 
 * - Manual work in this file: matching delete order to HabitHub data model,
 *   updating local user state after profile edits, and tuning messages and
 *   confirmation flow.
 * - REST and resource-handling ideas learned from course material are not
 *   marked here as AI.
 */

/**
 * Load current user profile from API.
 *
 * Input parameters:
 * - userId: Id of current logged user.
 *
 * Output:
 * - Returns user resource object from API.
 *
 * Exceptions / failure handling:
 * - API request errors are passed to caller so message can be shown.
 */
async function loadProfile(userId) {
  const { data: user } = await HabitHub.apiRequest(`/users/${userId}/`);
  return user;
}

/**
 * Delete user reminders, tracking logs, habits and in last the user.
 *
 * Input parameters:
 * - userId: Id of current logged user.
 *
 * Exceptions / failure handling:
 * - API request errors are passed if some delete step fails.
 * - Caller should catch error and show fail message to user.
 */
async function deleteAccountTree(userId) {
  const { data: habits } = await HabitHub.apiRequest(`/users/${userId}/habits/`);

  for (const habit of habits || []) {
    const { data: reminders } = await HabitHub.apiRequest(`/users/${userId}/habits/${habit.id}/reminders/`);
    for (const reminder of reminders || []) {
      await HabitHub.apiRequest(`/users/${userId}/habits/${habit.id}/reminders/${reminder.id}/`, {
        method: "DELETE",
      });
    }

    const { data: trackingLogs } = await HabitHub.apiRequest(`/users/${userId}/habits/${habit.id}/tracking/`);
    for (const tracking of trackingLogs || []) {
      await HabitHub.apiRequest(`/users/${userId}/habits/${habit.id}/tracking/${tracking.id}/`, {
        method: "DELETE",
      });
    }

    await HabitHub.apiRequest(`/users/${userId}/habits/${habit.id}/`, {
      method: "DELETE",
    });
  }

  await HabitHub.apiRequest(`/users/${userId}/`, {
    method: "DELETE",
  });
}

/**
 * Initialize settings page and connect profile/account actions.
 *
 *
 * Exceptions / failure handling:
 * - Protected page check uses HabitHub.requireUser and redirects if needed.
 * - API failures are caught in handlers and shown as flash message.
 */
async function initSettings() {
  const currentUser = HabitHub.requireUser();
  HabitHub.renderSidebar("settings");

  const form = document.getElementById("profileForm");
  const deleteBtn = document.getElementById("deleteUserBtn");

  try {
    const user = await loadProfile(currentUser.id);
    form.elements.first_name.value = user.first_name || "";
    form.elements.last_name.value = user.last_name || "";
    form.elements.email.value = user.email || "";
    HabitHub.setCurrentUser(user);
  } catch (error) {
    HabitHub.showMessage(error.message, "danger");
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = {
      first_name: String(form.elements.first_name.value || "").trim(),
      last_name: String(form.elements.last_name.value || "").trim(),
      email: String(form.elements.email.value || "").trim(),
    };

    try {
      await HabitHub.apiRequest(`/users/${currentUser.id}/`, {
        method: "PUT",
        body: payload,
      });
      HabitHub.setCurrentUser({ id: currentUser.id, ...payload });
      HabitHub.showMessage("Profile updated.", "success");
      HabitHub.renderSidebar("settings");
    } catch (error) {
      HabitHub.showMessage(error.message, "danger");
    }
  });

  deleteBtn.addEventListener("click", async () => {
    if (!window.confirm("Permanently delete your account? This cannot be undone.")) {
      return;
    }

    try {
      await deleteAccountTree(currentUser.id);
      HabitHub.clearCurrentUser();
      window.location.href = "/login.html";
    } catch (error) {
      HabitHub.showMessage(error.message, "danger");
    }
  });
}

document.addEventListener("DOMContentLoaded", initSettings);
