/* Dashboard page logic: stats, table, chart, and quick logging. */

let habitChartInstance = null;

function summarizeTracking(logs) {
  const toLocalDayKey = (dateObj) => {
    const year = dateObj.getFullYear();
    const month = String(dateObj.getMonth() + 1).padStart(2, "0");
    const day = String(dateObj.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
  };

  const now = new Date();
  const todayKey = toLocalDayKey(now);
  const day7 = new Date(now);
  day7.setDate(day7.getDate() - 6);
  const day30 = new Date(now);
  day30.setDate(day30.getDate() - 29);

  const uniqueDays = new Set();
  for (const log of logs) {
    const parsed = new Date(log.log_time);
    if (Number.isNaN(parsed.getTime())) {
      continue;
    }
    uniqueDays.add(toLocalDayKey(parsed));
  }

  let days7 = 0;
  let days30 = 0;
  for (const key of uniqueDays) {
    const dateObj = new Date(`${key}T00:00:00`);
    if (dateObj >= day7) {
      days7 += 1;
    }
    if (dateObj >= day30) {
      days30 += 1;
    }
  }

  let streak = 0;
  const cursor = new Date(now);
  while (true) {
    const key = toLocalDayKey(cursor);
    if (!uniqueDays.has(key)) {
      break;
    }
    streak += 1;
    cursor.setDate(cursor.getDate() - 1);
  }

  return {
    done_today: uniqueDays.has(todayKey),
    days7,
    days30,
    streak,
  };
}

function renderStats(doneCount, total, activeCount, bestStreak) {
  const statsGrid = document.getElementById("statsGrid");
  statsGrid.innerHTML = `
    <div class="stat-card">
      <div class="stat-val">${doneCount}<span style="font-size:1rem;color:var(--muted);font-weight:500;">/${total}</span></div>
      <div class="stat-label">Done today</div>
    </div>
    <div class="stat-card">
      <div class="stat-val">${activeCount}</div>
      <div class="stat-label">Active habits</div>
    </div>
    <div class="stat-card">
      <div class="stat-val">${bestStreak}</div>
      <div class="stat-label">Best streak</div>
    </div>
  `;
}

function renderHabitsTable(habits) {
  const mount = document.getElementById("habitsTableMount");
  if (!habits.length) {
    mount.innerHTML = '<p class="text-muted">No habits yet. Go to <a href="/habits.html">Habits</a> to create one.</p>';
    return;
  }

  const rows = habits.map((habit) => `
    <tr>
      <td><strong>${habit.name}</strong></td>
      <td>${habit.done_today ? '<span class="pill pill-ok">Done</span>' : '<span class="pill pill-no">Pending</span>'}</td>
      <td>${habit.streak} days</td>
      <td>${habit.days7}</td>
      <td>${habit.days30}</td>
      <td>${habit.active ? '<span class="pill pill-ok">Active</span>' : '<span class="pill pill-no">Inactive</span>'}</td>
      <td><button class="btn-sm" data-log-id="${habit.id}">Log now</button></td>
    </tr>
  `).join("");

  mount.innerHTML = `
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Status</th>
            <th>Streak</th>
            <th>7 days</th>
            <th>30 days</th>
            <th>Active</th>
            <th></th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
  `;
}

async function loadQuote() {
  const quoteLine = document.getElementById("quoteLine");
  try {
    const response = await fetch("https://zenquotes.io/api/random");
    const payload = await response.json();
    const entry = payload[0];
    quoteLine.textContent = `"${entry.q}" - ${entry.a}`;
  } catch {
    quoteLine.textContent = "Small steps every day build lasting habits.";
  }
}

function renderChart(habits) {
  const activeHabits = habits.filter((habit) => habit.active);
  const labels = activeHabits.map((habit) => habit.name);
  const days7 = activeHabits.map((habit) => habit.days7);
  const days30 = activeHabits.map((habit) => habit.days30);

  if (habitChartInstance) {
    habitChartInstance.destroy();
    habitChartInstance = null;
  }

  habitChartInstance = new Chart(document.getElementById("habitChart"), {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label: "7-day count",
          data: days7,
          backgroundColor: "rgba(99,102,241,0.75)",
          borderRadius: 6,
          borderSkipped: false,
        },
        {
          label: "30-day count",
          data: days30,
          backgroundColor: "rgba(99,102,241,0.2)",
          borderRadius: 6,
          borderSkipped: false,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: { position: "top" },
      },
      scales: {
        y: { beginAtZero: true, ticks: { precision: 0 } },
        x: { grid: { display: false } },
      },
    },
  });
}

function renderDashboard(habits, enriched) {
  const doneCount = enriched.filter((entry) => entry.done_today).length;
  const activeCount = habits.filter((entry) => entry.active).length;
  const bestStreak = enriched.reduce((max, entry) => Math.max(max, entry.streak), 0);

  renderStats(doneCount, habits.length, activeCount, bestStreak);
  renderHabitsTable(enriched);

  const activeHabits = enriched.filter((habit) => habit.active);
  const chartCanvas = document.getElementById("habitChart");
  let chartEmpty = document.getElementById("chartEmptyMessage");

  if (activeHabits.length) {
    if (chartEmpty) {
      chartEmpty.remove();
    }
    chartCanvas.style.display = "block";
    renderChart(enriched);
    return;
  }

  if (habitChartInstance) {
    habitChartInstance.destroy();
    habitChartInstance = null;
  }
  chartCanvas.style.display = "none";
  if (!chartEmpty) {
    chartEmpty = document.createElement("p");
    chartEmpty.id = "chartEmptyMessage";
    chartEmpty.className = "text-muted";
    chartCanvas.parentElement.appendChild(chartEmpty);
  }
  chartEmpty.textContent = "No active habits to chart.";
}

async function logHabit(userId, habitId) {
  await HabitHub.apiRequest(`/users/${userId}/habits/${habitId}/tracking/`, {
    method: "POST",
    body: { log_time: new Date().toISOString() },
  });
}

async function initDashboard() {
  const user = HabitHub.requireUser();
  HabitHub.renderSidebar("dashboard");
  document.getElementById("todayLine").textContent = new Date().toLocaleDateString(undefined, {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });
  loadQuote();

  try {
    const { data: habitsRaw } = await HabitHub.apiRequest(`/users/${user.id}/habits/`);
    const habits = habitsRaw || [];

    const activeHabits = habits.filter((habit) => habit.active);
    const activeMetrics = await Promise.all(
      activeHabits.map(async (habit) => {
        const { data: logs } = await HabitHub.apiRequest(`/users/${user.id}/habits/${habit.id}/tracking/`);
        return {
          id: habit.id,
          ...summarizeTracking(logs || []),
        };
      }),
    );
    const metricMap = new Map(activeMetrics.map((item) => [item.id, item]));

    const enriched = habits.map((habit) => {
      const metrics = metricMap.get(habit.id) || {
        done_today: false,
        days7: 0,
        days30: 0,
        streak: 0,
      };
      return { ...habit, ...metrics };
    });

    renderDashboard(habits, enriched);

    document.getElementById("habitsTableMount").addEventListener("click", async (event) => {
      const target = event.target;
      if (!(target instanceof HTMLElement)) {
        return;
      }
      const habitId = target.getAttribute("data-log-id");
      if (!habitId) {
        return;
      }
      try {
        await logHabit(user.id, habitId);
        HabitHub.showMessage("Habit logged!", "success");
        setTimeout(() => window.location.reload(), 350);
      } catch (error) {
        HabitHub.showMessage(error.message, "danger");
      }
    });
  } catch (error) {
    HabitHub.showMessage(error.message, "danger");
  }
}

document.addEventListener("DOMContentLoaded", initDashboard);
