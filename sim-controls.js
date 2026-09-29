/*
 * FloodLens – Simulate Flood / Reset wiring
 *
 * HTML needed on the map page:
 *   <button id="simulate-btn">Simulate Flood</button>
 *   <button id="reset-btn">Reset</button>
 *   <span id="sim-status" role="status" aria-live="polite"></span>
 *   <script src="sim-controls.js"></script>
 *
 * Ask the map teammate to expose ONE function: window.refreshMap()
 * (re-fetch risk + priorities + closed roads, redraw layers). Return a promise if possible.
 */
(() => {
  // ---- Config: match to backend endpoints ----
  const API_BASE = "";                       // "" = same origin, or "http://localhost:8000"
  const SIMULATE_URL = API_BASE + "/api/simulation/trigger-flood";
  const RESET_URL    = API_BASE + "/api/simulation/reset";
  const SNAPSHOT_URL = API_BASE + "/api/settlements";   // any GET that returns settlement risk/priority JSON
  // --------------------------------------------

  const simBtn = document.getElementById("simulate-btn");
  const resetBtn = document.getElementById("reset-btn");
  const statusEl = document.getElementById("sim-status");

  const say = (msg, isError = false) => {
    if (!statusEl) return;
    statusEl.textContent = msg;
    statusEl.style.color = isError ? "#b4530a" : "";
  };

  async function snapshot() {
    try {
      const r = await fetch(SNAPSHOT_URL, { cache: "no-store" });
      return r.ok ? JSON.stringify(await r.json()) : null;
    } catch { return null; }
  }

  async function refreshMap() {
    if (typeof window.refreshMap === "function") await window.refreshMap();
    window.dispatchEvent(new CustomEvent("floodlens:refresh"));   // fallback hook for teammates
  }

  async function run(url, label, expectChange) {
    const buttons = [simBtn, resetBtn].filter(Boolean);
    buttons.forEach((b) => (b.disabled = true));
    say(label + "…");
    try {
      const before = await snapshot();
      const res = await fetch(url, { method: "POST" });
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
      await refreshMap();
      const after = await snapshot();

      // Confirm the data really changed (skip if snapshot endpoint isn't available).
      if (expectChange && before && after && before === after) {
        say(label + " finished, but risk data didn't change. Check the backend or refreshMap().", true);
      } else {
        say(label + " done. Map updated at " + new Date().toLocaleTimeString() + ".");
      }
    } catch (err) {
      say(label + " failed: " + err.message, true);
      console.error(err);
    } finally {
      buttons.forEach((b) => (b.disabled = false));
    }
  }

  simBtn?.addEventListener("click", () => run(SIMULATE_URL, "Simulating flood", true));
  resetBtn?.addEventListener("click", () => run(RESET_URL, "Resetting", true));
})();
