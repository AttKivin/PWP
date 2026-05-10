/* Shared helpers used by all pages. */

const DEFAULT_API_KEY = "aleem";

function getApiKey() {
  return DEFAULT_API_KEY;
}

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

function setCurrentUser(user) {
  localStorage.setItem("habithubUser", JSON.stringify(user));
}

function clearCurrentUser() {
  localStorage.removeItem("habithubUser");
}

function requireUser() {
  const user = getCurrentUser();
  if (!user || !user.id) {
    window.location.href = "/login.html";
    throw new Error("User not logged in");
  }
  return user;
}

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

async function readErrorMessage(response) {
  let message = `API error ${response.status}`;
  try {
    const payload = await response.json();
    if (payload?.message) {
      return `${message}: ${payload.message}`;
    }
  } catch {
    // Ignore JSON parse failure.
  }

  try {
    const text = await response.text();
    if (text) {
      message = `${message}: ${text}`;
    }
  } catch {
    // Keep fallback message.
  }

  return message;
}

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
    const message = await readErrorMessage(response);
    throw new Error(message);
  }

  if (response.status === 204) {
    return { data: null, location: response.headers.get("Location") };
  }

  const contentType = response.headers.get("content-type") || "";
  const data = contentType.includes("application/json") ? await response.json() : await response.text();
  return { data, location: response.headers.get("Location") };
}

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
