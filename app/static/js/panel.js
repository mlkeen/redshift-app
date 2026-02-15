async function apiGet(url){
  const r = await fetch(url, {credentials:"include"});
  return r.json();
}
async function apiPost(url, body){
  const r = await fetch(url, {
    method:"POST",
    headers: {"Content-Type":"application/json"},
    credentials:"include",
    body: JSON.stringify(body)
  });
  return r.json();
}

function fmt(n){
  if (typeof n !== "number") return n;
  return n.toFixed(2);
}

function clear(el){ el.innerHTML = ""; return el; }

function makeToken(entity){
  const div = document.createElement("div");
  div.className = "token";
  div.draggable = true;
  div.dataset.entityId = entity.id;
  div.dataset.version = entity.version;

  const left = document.createElement("div");
  left.className = "name";
  left.textContent = entity.data?.name || entity.type_key;

  const right = document.createElement("div");
  right.className = "meta";
  right.textContent = "v" + entity.version;

  div.appendChild(left);
  div.appendChild(right);

  div.addEventListener("dragstart", (ev)=>{
    ev.dataTransfer.setData("application/json", JSON.stringify({id: entity.id, version: entity.version}));
  });

  return div;
}

let __lastSnapshot = null;

async function loadPanel(gameId, panelKey){
  __lastSnapshot = await apiGet(`/api/games/${gameId}/snapshot`);

  const snap = __lastSnapshot;

  // KPIs
  const ps = (snap.panel_states || []).find(x => x.panel_key === panelKey);
  const kCool = document.getElementById("kpi_coolant");
  const kAlert = document.getElementById("kpi_alert");
  if (ps && ps.state){
    if (kCool) kCool.textContent = fmt(ps.state.coolant_efficiency ?? 0);
    if (kAlert) kAlert.textContent = ps.state.alert ?? "—";
    const kHeat = document.getElementById("kpi_heat");
    if (kHeat) kHeat.textContent = fmt(ps.state.heat ?? 0);
  }

  // Render zones
  const zones = document.querySelectorAll("[data-zone]");
  zones.forEach(z => clear(z.querySelector(".zbody")));

  const ents = (snap.entities || []).filter(e => e.location?.panel === panelKey);
  ents.sort((a,b)=> (a.location.zone+a.location.pos).localeCompare(b.location.zone+b.location.pos));

  for (const e of ents){
    const zoneEl = document.querySelector(`[data-zone="${e.location.zone}"] .zbody`);
    if (zoneEl) zoneEl.appendChild(makeToken(e));
  }

  // Events
  const feed = document.getElementById("event_feed");
  if (feed){
    feed.innerHTML = "";
    for (const ev of (snap.events || [])){
      const line = document.createElement("div");
      line.className = "line";
      line.textContent = ev.message;
      feed.appendChild(line);
    }
  }
}

function wireDnD(gameId, panelKey){
  document.querySelectorAll(".zone").forEach(zoneEl=>{
    zoneEl.addEventListener("dragover", (ev)=>{ ev.preventDefault(); zoneEl.classList.add("over"); });
    zoneEl.addEventListener("dragleave", ()=> zoneEl.classList.remove("over"));
    zoneEl.addEventListener("drop", async (ev)=>{
      ev.preventDefault();
      zoneEl.classList.remove("over");
      const raw = ev.dataTransfer.getData("application/json");
      if (!raw) return;
      const data = JSON.parse(raw);
      const zone = zoneEl.dataset.zone;

      const r = await apiPost(`/api/games/${gameId}/commands`, {
        type: "MOVE_ENTITY",
        entity_id: data.id,
        expected_version: data.version,
        to: {panel: panelKey, zone: zone, pos: 0}
      });

      if (!r.ok){
        alert(r.error || "Move failed");
      }
      await loadPanel(gameId, panelKey);
    });
  });
}

window.RedshiftPanel = { loadPanel, wireDnD, apiGet, apiPost, getLastSnapshot };


function getLastSnapshot(){ return __lastSnapshot; }
