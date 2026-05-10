/*
 * Login and account creation code for static HabitHub client.
 *
 * Code origin:
 * - signInByEmail(): USER-WRITTEN. Implements email lookup and user matching logic
 *   with email normalization (trim, lowercase) for case-insensitive comparison.
 * - createAccount(): AI (Copilot GPT-5.4) with user adaptation to handle
 *   Location header follow-up and fallback to email-based sign-in.
 * - initLoginPage(): AI (Copilot GPT-5.4) with user adaptations for form wiring and API error display.
 *
 * Prompt reference: "Create client-side login and registration logic for a static frontend
 * that works with a REST API, stores the logged user locally, and redirects after success."
 */

/**
 * USER-WRITTEN: Sign in user by matching given email against user collection.
 *
 * Implementation:
 * - Fetches complete user collection from /users/ endpoint
 * - Normalizes input email (trim, lowercase) for case-insensitive comparison
 * - Finds matching user by normalized email
 * - Sets user session and redirects to dashboard
 *
 * Input parameters:
 * - email: Email value from sign-in form.
 *
 * Exceptions / failure handling:
 * - Throws Error if matching account is not found.
 * - Can pass API request errors from HabitHub.apiRequest.
 */

async function signInByEmail(email) {
  const { data: users } = await HabitHub.apiRequest("/users/");
  const normalized = email.trim().toLowerCase();
  const user = (users || []).find((entry) => (entry.email || "").toLowerCase() === normalized);
  if (!user) {
    throw new Error("No account found with that email.");
  }
  HabitHub.setCurrentUser(user);
  window.location.href = "/dashboard.html";
}

/**
 * AI (adapted by user): Create new user account with HabitHub API.
 *
 * Implementation:
 * - Posts new user payload to /users/ endpoint
 * - User adaptation: Follows Location header from POST response to fetch created user
 * - Extracts /users/{id}/ path from Location header and fetches user object
 * - Fallback: If Location follow-up fails, signs in by email instead
 * - Sets user session and redirects to dashboard
 *
 * Input parameters:
 * - payload: Object with first_name, last_name and email.
 *
 * Exceptions / failure handling:
 * - Can pass API request errors from create request or follow-up fetch.
 * - If Location follow-up does not give user object, code tries sign in by
 *   email as fallback.
 */

async function createAccount(payload) {
  const { location } = await HabitHub.apiRequest("/users/", {
    method: "POST",
    body: payload,
  });

  let user = null;
  if (location) {
    const relative = location.includes("/api/") ? location.substring(location.indexOf("/api") + 4) : null;
    if (relative) {
      const result = await HabitHub.apiRequest(relative);
      user = result.data;
    }
  }

  if (!user) {
    await signInByEmail(payload.email);
    return;
  }

  HabitHub.setCurrentUser(user);
  window.location.href = "/dashboard.html";
}

/**
 * AI (adapted by user): Add event handlers for sign-in and account creation forms.
 *
 * Implementation:
 * - Wires form submit events to call signInByEmail or createAccount
 * - User adaptations: Form error handling, flash message display
 * - Checks for existing session and redirects to dashboard if already logged in
 *
 * Exceptions / failure handling:
 * - If user already exists in local storage, page goes to dashboard.
 * - Form submit errors are caught and shown as flash message.
 */

function initLoginPage() {
  if (HabitHub.getCurrentUser()) {
    window.location.href = "/dashboard.html";
    return;
  }

  const signInForm = document.getElementById("signInForm");
  const createForm = document.getElementById("createForm");

  signInForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = new FormData(signInForm);
    const email = String(form.get("email") || "");
    try {
      await signInByEmail(email);
    } catch (error) {
      HabitHub.showMessage(error.message, "danger");
    }
  });

  createForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = new FormData(createForm);
    const payload = {
      first_name: String(form.get("first_name") || "").trim(),
      last_name: String(form.get("last_name") || "").trim(),
      email: String(form.get("email") || "").trim(),
    };

    if (!payload.first_name || !payload.last_name || !payload.email) {
      HabitHub.showMessage("All fields are required.", "warning");
      return;
    }

    try {
      await createAccount(payload);
    } catch (error) {
      HabitHub.showMessage(error.message, "danger");
    }
  });

}

document.addEventListener("DOMContentLoaded", initLoginPage);
