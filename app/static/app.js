"use strict";

// Calendar single-page app. No build step — plain ES modules-free script.

const MONTH_NAMES = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

const state = {
  user: null,            // { id, name }
  view: new Date(),      // any date within the displayed month
  counts: {},            // { "YYYY-MM-DD": numberOfNotes } for current month
};

// --- element refs ---------------------------------------------------------
const el = {
  app: document.getElementById("app"),
  greeting: document.getElementById("greeting"),
  monthLabel: document.getElementById("month-label"),
  grid: document.getElementById("grid"),
  prev: document.getElementById("prev-month"),
  next: document.getElementById("next-month"),

  nameOverlay: document.getElementById("name-overlay"),
  nameInput: document.getElementById("name-input"),
  nameSubmit: document.getElementById("name-submit"),
  nameError: document.getElementById("name-error"),

  dayOverlay: document.getElementById("day-overlay"),
  dayTitle: document.getElementById("day-title"),
  dayClose: document.getElementById("day-close"),
  noteBlocks: document.getElementById("note-blocks"),
  noteInput: document.getElementById("note-input"),
  noteAdd: document.getElementById("note-add"),
  noteError: document.getElementById("note-error"),
};

// --- helpers --------------------------------------------------------------
function pad(n) {
  return String(n).padStart(2, "0");
}

function ymd(year, month /* 0-based */, day) {
  return `${year}-${pad(month + 1)}-${pad(day)}`;
}

async function api(path, options) {
  const resp = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!resp.ok) {
    let detail = `Request failed (${resp.status})`;
    try {
      const body = await resp.json();
      if (body.detail) detail = typeof body.detail === "string" ? body.detail : detail;
    } catch (_) { /* ignore */ }
    throw new Error(detail);
  }
  return resp.json();
}

function show(node) { node.classList.remove("hidden"); }
function hide(node) { node.classList.add("hidden"); }

// --- auth -----------------------------------------------------------------
async function login(name) {
  const user = await api("/api/login", {
    method: "POST",
    body: JSON.stringify({ name }),
  });
  state.user = user;
  localStorage.setItem("calendar_user", JSON.stringify(user));
  el.greeting.textContent = `hello ${user.name}`;
  hide(el.nameOverlay);
  show(el.app);
  await renderMonth();
}

function promptForName() {
  show(el.nameOverlay);
  el.nameInput.focus();
}

async function submitName() {
  const name = el.nameInput.value.trim();
  if (!name) {
    el.nameError.textContent = "Please enter a name.";
    show(el.nameError);
    return;
  }
  try {
    await login(name);
  } catch (err) {
    el.nameError.textContent = err.message;
    show(el.nameError);
  }
}

// --- calendar rendering ---------------------------------------------------
async function renderMonth() {
  const year = state.view.getFullYear();
  const month = state.view.getMonth(); // 0-based

  el.monthLabel.textContent = `${MONTH_NAMES[month]} ${year}`;

  // Fetch note counts for this month.
  state.counts = {};
  try {
    const data = await api(`/api/notes?user_id=${state.user.id}&year=${year}&month=${month + 1}`);
    for (const note of data.notes) {
      state.counts[note.date] = (state.counts[note.date] || 0) + 1;
    }
  } catch (err) {
    console.error("Failed to load notes:", err);
  }

  buildGrid(year, month);
}

function buildGrid(year, month) {
  el.grid.innerHTML = "";

  const firstDay = new Date(year, month, 1);
  // Convert Sun=0..Sat=6 to Mon=0..Sun=6.
  const leading = (firstDay.getDay() + 6) % 7;
  const daysInMonth = new Date(year, month + 1, 0).getDate();

  const today = new Date();
  const todayKey = ymd(today.getFullYear(), today.getMonth(), today.getDate());

  for (let i = 0; i < leading; i++) {
    const blank = document.createElement("div");
    blank.className = "cell empty";
    el.grid.appendChild(blank);
  }

  for (let day = 1; day <= daysInMonth; day++) {
    const key = ymd(year, month, day);
    const cell = document.createElement("div");
    cell.className = "cell";
    const weekday = new Date(year, month, day).getDay(); // 0 Sun .. 6 Sat
    if (weekday === 0 || weekday === 6) cell.classList.add("weekend");
    if (key === todayKey) cell.classList.add("today");

    const num = document.createElement("span");
    num.className = "day-num";
    num.textContent = day;
    cell.appendChild(num);

    const count = state.counts[key];
    if (count) {
      const badge = document.createElement("div");
      badge.className = "badge";
      badge.innerHTML = `<span class="dot"></span><span>${count}</span>`;
      cell.appendChild(badge);
    }

    cell.addEventListener("click", () => openDay(key));
    el.grid.appendChild(cell);
  }
}

// --- day popup ------------------------------------------------------------
let activeDate = null;

async function openDay(dateKey) {
  activeDate = dateKey;
  el.dayTitle.textContent = dateKey;
  el.noteInput.value = "";
  hide(el.noteError);
  el.noteBlocks.innerHTML = `<p class="note-empty">Loading...</p>`;
  show(el.dayOverlay);
  el.noteInput.focus();
  await loadDayNotes(dateKey);
}

async function loadDayNotes(dateKey) {
  const [year, month] = dateKey.split("-").map(Number);
  try {
    const data = await api(`/api/notes?user_id=${state.user.id}&year=${year}&month=${month}`);
    const dayNotes = data.notes.filter((n) => n.date === dateKey);
    renderDayNotes(dayNotes);
  } catch (err) {
    el.noteBlocks.innerHTML = `<p class="note-empty">Failed to load notes.</p>`;
  }
}

function renderDayNotes(notes) {
  el.noteBlocks.innerHTML = "";
  if (notes.length === 0) {
    el.noteBlocks.innerHTML = `<p class="note-empty">No notes yet for this day.</p>`;
    return;
  }
  for (const note of notes) {
    const block = document.createElement("div");
    block.className = "note-block";

    const text = document.createElement("span");
    text.className = "note-text";
    text.textContent = note.content;
    block.appendChild(text);

    const del = document.createElement("button");
    del.className = "note-del";
    del.title = "Delete note";
    del.setAttribute("aria-label", "Delete note");
    del.innerHTML = "&times;";
    del.addEventListener("click", () => deleteNote(note.id));
    block.appendChild(del);

    el.noteBlocks.appendChild(block);
  }
}

async function deleteNote(noteId) {
  try {
    await api(`/api/notes/${noteId}?user_id=${state.user.id}`, { method: "DELETE" });
    hide(el.noteError);
    await loadDayNotes(activeDate);
    state.counts[activeDate] = Math.max(0, (state.counts[activeDate] || 1) - 1);
    if (state.counts[activeDate] === 0) delete state.counts[activeDate];
    buildGrid(state.view.getFullYear(), state.view.getMonth());
  } catch (err) {
    el.noteError.textContent = err.message;
    show(el.noteError);
  }
}

async function addNote() {
  const content = el.noteInput.value.trim();
  if (!content) {
    el.noteError.textContent = "Note can't be empty.";
    show(el.noteError);
    return;
  }
  try {
    await api("/api/notes", {
      method: "POST",
      body: JSON.stringify({ user_id: state.user.id, date: activeDate, content }),
    });
    el.noteInput.value = "";
    hide(el.noteError);
    await loadDayNotes(activeDate);
    state.counts[activeDate] = (state.counts[activeDate] || 0) + 1;
    buildGrid(state.view.getFullYear(), state.view.getMonth());
  } catch (err) {
    el.noteError.textContent = err.message;
    show(el.noteError);
  }
}

function closeDay() {
  hide(el.dayOverlay);
  activeDate = null;
}

// --- wiring ---------------------------------------------------------------
el.nameSubmit.addEventListener("click", submitName);
el.nameInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") submitName();
});

el.prev.addEventListener("click", async () => {
  state.view = new Date(state.view.getFullYear(), state.view.getMonth() - 1, 1);
  await renderMonth();
});
el.next.addEventListener("click", async () => {
  state.view = new Date(state.view.getFullYear(), state.view.getMonth() + 1, 1);
  await renderMonth();
});

el.dayClose.addEventListener("click", closeDay);
el.dayOverlay.addEventListener("click", (e) => {
  if (e.target === el.dayOverlay) closeDay();
});
el.noteAdd.addEventListener("click", addNote);
el.noteInput.addEventListener("keydown", (e) => {
  // Ctrl/Cmd+Enter submits.
  if ((e.ctrlKey || e.metaKey) && e.key === "Enter") addNote();
});

// --- boot -----------------------------------------------------------------
(async function init() {
  const saved = localStorage.getItem("calendar_user");
  if (saved) {
    try {
      const user = JSON.parse(saved);
      // Re-confirm with the server (handles a wiped database gracefully).
      await login(user.name);
      return;
    } catch (_) {
      localStorage.removeItem("calendar_user");
    }
  }
  promptForName();
})();
