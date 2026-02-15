function pad(n){ return String(n).padStart(2, "0"); }

function fmtSeconds(s){
  s = Math.max(0, Math.floor(s));
  const h = Math.floor(s/3600);
  const m = Math.floor((s%3600)/60);
  const sec = s%60;
  if (h > 0) return `${pad(h)}:${pad(m)}:${pad(sec)}`;
  return `${pad(m)}:${pad(sec)}`;
}

async function fetchTime(gameId){
  const r = await fetch(`/games/${gameId}/time`, {credentials:"same-origin"});
  return await r.json();
}

function parseIso(s){
  if (!s) return null;
  // handles "Z" or local isoformat
  return new Date(s);
}

function init(gameId){
  const label = document.getElementById("timer_label");
  const value = document.getElementById("timer_value");
  const ticklen = document.getElementById("timer_ticklen");
  const sub = document.getElementById("timer_sub");
  const tickValue = document.getElementById("tick_value");

  let state = null;
  let lastFetch = 0;

  async function refresh(){
    state = await fetchTime(gameId);
    lastFetch = Date.now();
  }

  function render(){
    if (!state || !state.ok) return;

    const now = new Date(); // client time; we'll refresh periodically to avoid drift
    const startAt = parseIso(state.start_at);
    const startedAt = parseIso(state.started_at);
    const tl = parseInt(state.tick_length_seconds || 120, 10);

    if (ticklen) ticklen.textContent = `${tl}s`;
    if (tickValue) tickValue.textContent = (state.ticks_elapsed ?? "—");

    // Not started yet → countdown to scheduled start
    if (!startedAt){
      if (startAt){
        const secs = (startAt.getTime() - now.getTime()) / 1000;
        if (label) label.textContent = "STARTS IN";
        if (value) value.textContent = fmtSeconds(secs);
        if (sub) sub.textContent = `Scheduled: ${startAt.toLocaleString()}`;
      } else {
        if (label) label.textContent = "NOT STARTED";
        if (value) value.textContent = "—";
        if (sub) sub.textContent = "No start time set.";
      }
      return;
    }

    // Started → countdown to next tick boundary
    const elapsed = (now.getTime() - startedAt.getTime()) / 1000;
    const intoTick = ((elapsed % tl) + tl) % tl;
    const remaining = tl - intoTick;

    if (label) label.textContent = "NEXT TICK IN";
    if (value) value.textContent = fmtSeconds(remaining);
    if (sub) sub.textContent = `Started: ${startedAt.toLocaleString()}`;
  }

  // initial load
  refresh().then(render);

  // render every second
  setInterval(render, 1000);

  // re-sync time/state every 15s
  setInterval(async ()=>{
    try { await refresh(); } catch(e) {}
  }, 15000);
}

window.RedshiftTimer = { init };
