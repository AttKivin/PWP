/*
 * Shared client utilities. API requests, localStorage session, messages, sidebar.
 * getApiKey, getCurrentUser, setCurrentUser, clearCurrentUser, requireUser, formatDate: me
 * apiRequest, renderSidebar, showMessage: AI scaffold, tweaked by me
 */

const DEFAULT_API_KEY = "aleem";

/**
 * Get API key string for X-API-KEY header.
 */
function getApiKey() {
  return DEFAULT_API_KEY;
}

/**
 * Get logged user from local storage. Returns null if missing or broken.
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
 * Save user to local storage.
 */
function setCurrentUser(user) {
  localStorage.setItem("habithubUser", JSON.stringify(user));
}

/**
 * Clear user from local storage.
 */
function clearCurrentUser() {
  localStorage.removeItem("habithubUser");
}

/**
 * Check if user is logged in. Redirect to login if not.
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
 * Show a flash message. Type: info, success, warning, danger.
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
 * Send HTTP request to /api. Returns data and Location header.
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
 * Render sidebar with nav links and user info.
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
        <a href="#" id="switchUserBtn">Log out</a>
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
 * Extract YYYY-MM-DD from ISO timestamp. Return "-" if missing.
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
