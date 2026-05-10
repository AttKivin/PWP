/* Login and registration page logic. */


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
