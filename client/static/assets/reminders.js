/*
 * Reminder management page code for static HabitHub client.
 *
 * AI use and code origin:
 * - AI used: GitHub Copilot with GPT-5.4.
 * 
 * - Prompt summary used for AI-assisted parts:
 *   "Build client-side reminder management for a static frontend, including
 *   loading habit id from query string and create, edit, delete reminder
 *   actions."
 * 
 * - AI-assisted methods in this file: initReminders.
 * 
 * - Manual work in this file: adapting URL/query behavior to HabitHub pages,
 *   handling reminder time fields, and matching API endpoints and messages.
 */

/**
 * Read habit id from page query string.
 *
 * Output:
 * - Returns habitId from query as string, or null if missing
 */
function getHabitIdFromQuery() {
  const params = new URLSearchParams(window.location.search);
  return params.get("habitId");
}

/**
 * Build reminder table HTML for selected habit.
 *
 * Input parameters:
 * - reminders: Array of reminder resources from API.
 * - habitId: Selected habit id from page query.
 *
 * Output:
 * - Returns HTML string for reminder table or empty message.
 */
function renderReminderTable(reminders, habitId) {
  if (!reminders.length) {
    return '<p class="text-muted">No reminders yet. Add one above.</p>';
  }
  const rows = reminders.map((reminder) => `
    <tr>
      <td><strong>${reminder.reminded_time}</strong></td>
      <td style="color:var(--muted);">${HabitHub.formatDate(reminder.creation_date)}</td>
      <td>
        <form class="form-row" style="flex-wrap:nowrap;" data-edit-id="${reminder.id}">
          <input type="time" name="reminded_time" value="${reminder.reminded_time}" required>
          <button type="submit" class="btn-secondary btn-sm">Save</button>
        </form>
      </td>
      <td><button class="btn-danger btn-sm" data-delete-id="${reminder.id}">Delete</button></td>
    </tr>
  `).join("");

  return `
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Time</th>
            <th>Created</th>
            <th>Edit</th>
            <th>Delete</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
  `;
}

/**
 * Refresh reminders for selected habit and render table again.
 *
 * Input parameters:
 * - userId: Id of current logged user.
 * - habitId: Id of selected habit.
 *
 *
 * Exceptions / failure handling:
 * - API request errors are passed to caller so flash message can be shown.
 */
async function refreshReminders(userId, habitId) {
  const { data: reminders } = await HabitHub.apiRequest(`/users/${userId}/habits/${habitId}/reminders/`);
  document.getElementById("remindersMount").innerHTML = renderReminderTable(reminders || [], habitId);
}

/**
 * Initialize reminders page and register CRUD handlers.
 *
 * Exceptions / failure handling:
 * - Login protection is done by HabitHub.requireUser.
 * - Missing query parameter and API failures are shown by flash message and
 *   function returns early.
 */
async function initReminders() {
  const user = HabitHub.requireUser();
  HabitHub.renderSidebar("habits");

  const habitId = getHabitIdFromQuery();
  if (!habitId) {
    HabitHub.showMessage("Missing habitId query parameter.", "danger");
    return;
  }

  try {
    const { data: habit } = await HabitHub.apiRequest(`/users/${user.id}/habits/${habitId}/`);
    document.getElementById("habitName").textContent = habit.name;
  } catch (error) {
    HabitHub.showMessage(error.message, "danger");
    return;
  }

  const addForm = document.getElementById("addReminderForm");
  addForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = new FormData(addForm);
    const remindedTime = String(form.get("reminded_time") || "").trim();
    if (!remindedTime) {
      HabitHub.showMessage("Time is required.", "warning");
      return;
    }

    try {
      await HabitHub.apiRequest(`/users/${user.id}/habits/${habitId}/reminders/`, {
        method: "POST",
        body: { reminded_time: remindedTime },
      });
      addForm.reset();
      HabitHub.showMessage("Reminder added.", "success");
      await refreshReminders(user.id, habitId);
    } catch (error) {
      HabitHub.showMessage(error.message, "danger");
    }
  });

  const mount = document.getElementById("remindersMount");
  mount.addEventListener("submit", async (event) => {
    const form = event.target;
    if (!(form instanceof HTMLFormElement)) {
      return;
    }
    const reminderId = form.getAttribute("data-edit-id");
    if (!reminderId) {
      return;
    }

    event.preventDefault();
    const formData = new FormData(form);
    const remindedTime = String(formData.get("reminded_time") || "").trim();

    try {
      await HabitHub.apiRequest(`/users/${user.id}/habits/${habitId}/reminders/${reminderId}/`, {
        method: "PUT",
        body: { reminded_time: remindedTime },
      });
      HabitHub.showMessage("Reminder updated.", "success");
      await refreshReminders(user.id, habitId);
    } catch (error) {
      HabitHub.showMessage(error.message, "danger");
    }
  });

  mount.addEventListener("click", async (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement)) {
      return;
    }
    const reminderId = target.getAttribute("data-delete-id");
    if (!reminderId) {
      return;
    }

    if (!window.confirm("Delete this reminder?")) {
      return;
    }

    try {
      await HabitHub.apiRequest(`/users/${user.id}/habits/${habitId}/reminders/${reminderId}/`, {
        method: "DELETE",
      });
      HabitHub.showMessage("Reminder deleted.", "success");
      await refreshReminders(user.id, habitId);
    } catch (error) {
      HabitHub.showMessage(error.message, "danger");
    }
  });

  try {
    await refreshReminders(user.id, habitId);
  } catch (error) {
    HabitHub.showMessage(error.message, "danger");
  }
}

document.addEventListener("DOMContentLoaded", initReminders);
