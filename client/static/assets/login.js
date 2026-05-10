/*
 * Login and account creation code for static HabitHub client.
 *
 * AI use and code origin:
 * - AI used: GitHub Copilot with GPT-5.4.
 * 
 * - Prompt summary used for AI-assisted parts:
 *   "Create client-side login and registration logic for a static frontend
 *   that works with a REST API, stores the logged user locally, and redirects
 *   after success."
 * 
 * - AI-assisted methods in this file: createAccount.
 * 
 * - Manual work in this file: matching sign-in to HabitHub email flow,
 *   following Location header format from this API, and simplifying login page
 *   after removing developer-only API key input.
 */


/**
 * Sign in user by finding email from user collection.
 *
 * Input parameters:
 * - email: Email address written in login form.
 *
 * Exceptions / failure handling:
 * - Throws Error if matching account is not found.
 * - Can also pass API request error from HabitHub.apiRequest.
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
 * Create new user account with HabitHub API.
 *
 * Input parameters:
 * - payload: Object with first_name, last_name and email.
 *
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
 * Add event handlers for login and create account forms.
 *
 * Exceptions / failure handling:
 * - If user already exists in local storage, page goes direct to dashboard.
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
