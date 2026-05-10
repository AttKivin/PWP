/*
 * Habit management page code for static HabitHub client.
 *
 * Code origin:
 * - All functions: AI (Copilot GPT-5.4) with user manual work.
 * - User adaptations: Field names and API endpoints mapped to HabitHub model,
 *   CRUD event handlers wired manually, reminder links integrated.
 *
 * Prompt reference: "Build client-side CRUD page logic for habits in a static web frontend,
 * including table rendering, create form, update form, and delete actions. Make sure to
 * adapt API requests and field names to match HabitHub API."
 */

let cachedHabits = [];

/**
 * AI (adapted): Build HTML table text from current habit collection.
 *
 * Input parameters:
 * - habits: Array of habit resources from API.
 *
 * Output:
 * - Returns HTML string for table or empty message.
 *
 * User adaptation: Reminder links wired to reminders.html with habitId query parameter,
 * field names and styling adapted to HabitHub model.
 *
 * Exceptions / failure handling:
 * - This function should not fail in normal use. It expects habit fields same
 *   like HabitHub API returns.
 */
function habitsTableHtml(habits) {
  if (!habits.length) {
    return '<p class="text-muted">No habits yet. Add one above to get started.</p>';
  }

  const rows = habits.map((habit) => `
    <tr>
      <td><strong>${habit.name}</strong></td>
      <td>${habit.active ? '<span class="pill pill-ok">Active</span>' : '<span class="pill pill-no">Inactive</span>'}</td>
      <td style="color:var(--muted);">${HabitHub.formatDate(habit.creation_date)}</td>
      <td><a href="/reminders.html?habitId=${habit.id}">Reminders &rarr;</a></td>
      <td>
        <form class="form-row" style="flex-wrap:nowrap;" data-edit-id="${habit.id}">
          <input name="name" value="${habit.name}" required style="width:130px;">
          <label style="display:flex;align-items:center;gap:5px;font-size:0.82rem;color:var(--muted);cursor:pointer;white-space:nowrap;">
            <input type="checkbox" name="active" value="1" ${habit.active ? "checked" : ""}> Active
          </label>
          <button type="submit" class="btn-secondary btn-sm">Save</button>
        </form>
      </td>
      <td><button class="btn-danger btn-sm" data-delete-id="${habit.id}">Delete</button></td>
    </tr>
  `).join("");

  return `
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Active</th>
            <th>Created</th>
            <th>Reminders</th>
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
 * AI (adapted): Refresh habit list from API and render table again.
 *
 * Input parameters:
 * - userId: Id of current logged user.
 *
 * Exceptions / failure handling:
 * - API request errors are passed to caller so message can be shown.
 */
async function refreshHabits(userId) {
  const { data: habits } = await HabitHub.apiRequest(`/users/${userId}/habits/`);
  cachedHabits = habits || [];
  document.getElementById("habitsMount").innerHTML = habitsTableHtml(cachedHabits);
}

/**
 * AI (adapted): Initialize habits page and connect all CRUD event handlers.
 *
 * User adaptations: All form submit and click event handlers wired manually to wire
 * create, update, delete operations with proper form validation and API endpoint routing.
 *
 * Exceptions / failure handling:
 * - Protected page check uses HabitHub.requireUser and redirects if needed.
 * - API failures are caught in handlers and shown as flash message.
 */
async function initHabits() {
  const user = HabitHub.requireUser();
  HabitHub.renderSidebar("habits");

  const addForm = document.getElementById("addHabitForm");
  addForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = new FormData(addForm);
    const name = String(form.get("name") || "").trim();
    if (!name) {
      HabitHub.showMessage("Habit name cannot be empty.", "warning");
      return;
    }

    try {
      await HabitHub.apiRequest(`/users/${user.id}/habits/`, {
        method: "POST",
        body: { name, active: true },
      });
      addForm.reset();
      HabitHub.showMessage(`Habit '${name}' created.`, "success");
      await refreshHabits(user.id);
    } catch (error) {
      HabitHub.showMessage(error.message, "danger");
    }
  });

  const mount = document.getElementById("habitsMount");
  mount.addEventListener("submit", async (event) => {
    const form = event.target;
    if (!(form instanceof HTMLFormElement)) {
      return;
    }
    const habitId = form.getAttribute("data-edit-id");
    if (!habitId) {
      return;
    }

    event.preventDefault();
    const data = new FormData(form);
    const payload = {
      name: String(data.get("name") || "").trim(),
      active: data.get("active") === "1",
    };

    try {
      await HabitHub.apiRequest(`/users/${user.id}/habits/${habitId}/`, {
        method: "PUT",
        body: payload,
      });
      HabitHub.showMessage("Habit updated.", "success");
      await refreshHabits(user.id);
    } catch (error) {
      HabitHub.showMessage(error.message, "danger");
    }
  });

  mount.addEventListener("click", async (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement)) {
      return;
    }
    const habitId = target.getAttribute("data-delete-id");
    if (!habitId) {
      return;
    }
    if (!window.confirm("Delete this habit and all its data?")) {
      return;
    }
    try {
      await HabitHub.apiRequest(`/users/${user.id}/habits/${habitId}/`, {
        method: "DELETE",
      });
      HabitHub.showMessage("Habit deleted.", "success");
      await refreshHabits(user.id);
    } catch (error) {
      HabitHub.showMessage(error.message, "danger");
    }
  });

  try {
    await refreshHabits(user.id);
  } catch (error) {
    HabitHub.showMessage(error.message, "danger");
  }
}

document.addEventListener("DOMContentLoaded", initHabits);
