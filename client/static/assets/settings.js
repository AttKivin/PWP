/*
 * Settings and account management code for static HabitHub client.
 *
 * Code origin:
 * - loadProfile(): USER-WRITTEN. Simple API request to load user profile by id.
 * - deleteAccountTree(): AI scaffold structure, USER IMPLEMENTED the correct cascading
 *   delete order based on HabitHub data model: reminders → tracking logs → habits → user.
 *   This order ensures foreign key constraints are satisfied during deletion.
 * - initSettings(): AI scaffold with user adaptations for form wiring and session state updates.
 *
 * Prompt: "Create client-side settings page logic for profile updates and account
 * deletion in a static frontend that talks to a REST API."
 *
 * REST and resource-handling patterns from course material
 */

/**
 * USER-WRITTEN: Load current user profile from API.
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
 * AI-SCAFFOLD (user-implemented cascade order): Delete user reminders, tracking logs, habits and user.
 *
 * Input parameters:
 * - userId: Id of current logged user.
 *
 * USER IMPLEMENTATION:
 * Correct cascading delete because of Habithub bug where deleting user does not cascade 
 * to habits, and deleting habits does not cascade to reminders and tracking logs. 
 * The correct order is:
 * 1. Delete all reminders for each habit (references habit)
 * 2. Delete all tracking logs for each habit (references habit)
 * 3. Delete all habits (references user)
 * 4. Delete user account
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
 * ChatGPT 5.4 (adapted): Initialize settings page and connect profile/account actions.
 *
 * Implementation:
 * - Loads current user profile into form fields
 * - Wires profile update form submission with PUT request
 * - Updates local session after profile changes
 * - Wires account delete button with confirmation and cascading delete
 * - Error handling for all operations
 *
 * User adaptations: Session state updates after profile edit, delete order management.
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
