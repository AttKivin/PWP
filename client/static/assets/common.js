/*
 * Shared helper code for static HabitHub client.
 *
 * AI use and code origin:
 * - AI used: GitHub Copilot with GPT-5.4.
 * - Prompt summary used for AI-assisted parts:
 *   "Create shared client utilities for a static HabitHub frontend with API
 *   request helper, localStorage user session handling, flash messages, and
 *   sidebar rendering."
 * - AI-assisted methods in this file: apiRequest and renderSidebar.
 * - Manual work in this file: adapting request flow to HabitHub proxy,
 *   matching sidebar links to this project pages, and adjusting messages and
 *   storage keys.
 * - REST client ideas learned from course material are not marked here as AI.
 * - AI was used only for some harder utility structure and request flow.
 */

const DEFAULT_API_KEY = "aleem";

/**
 * Get API key for proxied API request.
 *
 * Input parameters:
 * - None.
 *
 * Output:
 * - Returns API key string for X-API-KEY header.
 *
 * Exceptions / failure handling:
 * - This function should not fail in normal case.
 */
function getApiKey() {
  return DEFAULT_API_KEY;
}

/**
 * Read logged user object from browser local storage.
 *
 * Input parameters:
 * - None.
 *
 * Output:
 * - Returns parsed user object if it exists.
 * - Returns null if user is missing or saved JSON is broken.
 *
 * Exceptions / failure handling:
 * - JSON parse error is caught and function returns null.
 */
function getCurrentUser() {
  const raw = localStorage.getItem("habithubUser");
  if (!raw) {
    return null;
  }
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

/**
 * Save logged user object to browser local storage.
 *
 * Input parameters:
 * - user: User object from HabitHub API.
 *
 * Output:
 * - No return value.
 *
 * Exceptions / failure handling:
 * - If browser storage is blocked, runtime error can happen.
 */
function setCurrentUser(user) {
  localStorage.setItem("habithubUser", JSON.stringify(user));
}

/**
 * Remove logged user object from browser local storage.
 *
 * Input parameters:
 * - None.
 *
 * Output:
 * - No return value.
 *
 * Exceptions / failure handling:
 * - If browser storage is blocked, runtime error can happen.
 */
function clearCurrentUser() {
  localStorage.removeItem("habithubUser");
}

/**
 * Check that protected page has logged user.
 *
 * Input parameters:
 * - None.
 *
 * Output:
 * - Returns current user object if login data exists.
 *
 * Exceptions / failure handling:
 * - If user is missing, page goes to login and function throws Error.
 */
function requireUser() {
  const user = getCurrentUser();
  if (!user || !user.id) {
    window.location.href = "/login.html";
    throw new Error("User not logged in");
  }
  return user;
}

/**
 * Show temporary message in page.
 *
 * Input parameters:
 * - text: Message text for user.
 * - type: Message style like info, success, warning or danger.
 *
 * Output:
 * - No return value.
 *
 * Exceptions / failure handling:
 * - If page has no flash container, function just ends.
 */
function showMessage(text, type = "info") {
  const wrap = document.getElementById("flashWrap");
  if (!wrap) {
    return;
  }
  wrap.innerHTML = "";
  const box = document.createElement("div");
  box.className = `msg msg-${type}`;
  box.textContent = text;
  wrap.appendChild(box);
  setTimeout(() => {
    if (wrap.contains(box)) {
      wrap.removeChild(box);
    }
  }, 4500);
}

/**
 * Send HTTP request to proxied HabitHub API.
 *
 * Input parameters:
 * - path: API path after /api, for example /users/.
 * - options: Optional request data with method and JSON body.
 *
 * Output:
 * - Returns object with parsed response data and maybe Location header.
 *
 * Exceptions / failure handling:
 * - Throws Error if HTTP response is not successful.
 * - Reads JSON or text error body and makes readable message from it.
 */
async function apiRequest(path, options = {}) {
  const { method = "GET", body = null } = options;
  const headers = {
    "X-API-KEY": getApiKey(),
  };
  if (body !== null) {
    headers["Content-Type"] = "application/json";
  }

  const response = await fetch(`/api${path}`, {
    method,
    headers,
    body: body !== null ? JSON.stringify(body) : null,
  });

  if (!response.ok) {
    let message = `API error ${response.status}`;
    try {
      const payload = await response.json();
      if (payload && payload.message) {
        message = `${message}: ${payload.message}`;
      }
    } catch {
      try {
        const text = await response.text();
        if (text) {
          message = `${message}: ${text}`;
        }
      } catch {
        // Ignore body parse errors.
      }
    }
    throw new Error(message);
  }

  if (response.status === 204) {
    return { data: null, location: response.headers.get("Location") };
  }

  const contentType = response.headers.get("content-type") || "";
  const data = contentType.includes("application/json") ? await response.json() : await response.text();
  return { data, location: response.headers.get("Location") };
}

/**
 * Render shared sidebar for pages after login.
 *
 * Input parameters:
 * - activePage: Name of page which is active now.
 *
 * Output:
 * - No return value.
 *
 * Exceptions / failure handling:
 * - If user is missing, page goes to login.
 * - If sidebar mount is missing, function just ends.
 */
function renderSidebar(activePage) {
  const mount = document.getElementById("sidebarMount");
  if (!mount) {
    return;
  }
  const user = getCurrentUser();
  if (!user) {
    window.location.href = "/login.html";
    return;
  }

  mount.innerHTML = `
    <div class="sidebar">
      <div class="sidebar-brand">
        <div class="logo">HabitHub</div>
        <div class="tagline">Habit tracking client</div>
      </div>
      <nav class="sidebar-nav">
        <a href="/dashboard.html" class="${activePage === "dashboard" ? "active" : ""}"><span class="ni">D</span> Dashboard</a>
        <a href="/habits.html" class="${activePage === "habits" ? "active" : ""}"><span class="ni">H</span> Habits</a>
        <a href="/settings.html" class="${activePage === "settings" ? "active" : ""}"><span class="ni">S</span> Settings</a>
      </nav>
      <div class="sidebar-footer">
        <div class="sidebar-user">${user.first_name || ""} ${user.last_name || ""}</div>
        <a href="#" id="switchUserBtn">Switch user</a>
      </div>
    </div>
  `;

  const switchBtn = document.getElementById("switchUserBtn");
  if (switchBtn) {
    switchBtn.addEventListener("click", (event) => {
      event.preventDefault();
      clearCurrentUser();
      window.location.href = "/login.html";
    });
  }
}

/**
 * Change ISO-like date string to short YYYY-MM-DD text.
 *
 * Input parameters:
 * - isoLike: Date-time string or similar value from API.
 *
 * Output:
 * - Returns short YYYY-MM-DD string.
 * - Returns "-" if value is missing.
 *
 * Exceptions / failure handling:
 * - Full date validation is not done here. Function only cuts string because
 *   API already gives ISO-like timestamp.
 */
function formatDate(isoLike) {
  if (!isoLike) {
    return "-";
  }
  return String(isoLike).slice(0, 10);
}

window.HabitHub = {
  apiRequest,
  clearCurrentUser,
  formatDate,
  getCurrentUser,
  renderSidebar,
  requireUser,
  setCurrentUser,
  showMessage,
};
