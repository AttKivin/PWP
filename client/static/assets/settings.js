/* Settings page logic: profile update and account deletion. */

async function loadProfile(userId) {
  const { data: user } = await HabitHub.apiRequest(`/users/${userId}/`);
  return user;
}

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
