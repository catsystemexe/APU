const chatEl = document.getElementById("chat");
const inputEl = document.getElementById("input");
const sendBtn = document.getElementById("send");
const clearBtn = document.getElementById("btnClear");
const personalBtn = document.getElementById("btnPersonal");
const copyNotepadBtn = document.getElementById("btnCopyNotepad");
const copySessionBtn = document.getElementById("btnCopySession");
const llmExtractionToggle = document.getElementById("llmExtractionToggle");
const sessionStatsEl = document.getElementById("sessionStats");
const notepadEl = document.getElementById("notepad");
const caseIdLabelEl = document.getElementById("caseIdLabel");

let currentCaseId = null;
let latestCaseState = null;
let sessionTurns = [];

let session = {
  est_in_tokens: 0,
  est_out_tokens: 0,
  est_total_tokens: 0,
  est_cost_usd: null,
};

function fmtInt(n){
  return (n ?? 0).toLocaleString("cs-CZ");
}

function updateSessionStats(){
  if (!sessionStatsEl) return;
  const cost = session.est_cost_usd;
  const costStr = (cost == null) ? "—" : `$${cost.toFixed(4)}`;
  sessionStatsEl.textContent =
    `Session: ~${fmtInt(session.est_total_tokens)} tok (in ~${fmtInt(session.est_in_tokens)} / out ~${fmtInt(session.est_out_tokens)}) · cost ${costStr}`;
}

function setCaseId(caseId){
  currentCaseId = caseId || currentCaseId;
  if (caseIdLabelEl) {
    caseIdLabelEl.textContent = `case: ${currentCaseId || "—"}`;
  }
}

function addMessage(role, text, {loading=false} = {}) {
  const wrap = document.createElement("div");
  wrap.className = `msg ${role}`;

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = role === "user" ? "U" : "APU";

  const content = document.createElement("div");
  content.className = "msgContent";

  const bubble = document.createElement("div");
  bubble.className = "bubble" + (loading ? " loading" : "");
  bubble.textContent = text;

  content.appendChild(bubble);
  wrap.appendChild(avatar);
  wrap.appendChild(content);
  chatEl.appendChild(wrap);
  chatEl.scrollTop = chatEl.scrollHeight;

  return {wrap, content, bubble};
}

function renderAssistantBubble(bubbleEl, text) {
  bubbleEl.textContent = "";

  const sectionLabels = [
    "Shrnutí:",
    "Pracovní interpretace:",
    "Doporučený postup:",
    "Ověření:",
    "Možnosti:",
    "Chybí upřesnit:",
    "Doporučené zaměření:"
  ];

  const lines = String(text || "").split("\n");

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (line.trim() === "") continue;

    const matched = sectionLabels.find(label => line.startsWith(label));

    if (matched) {
      if (bubbleEl.childNodes.length > 0) bubbleEl.appendChild(document.createElement("br"));

      const label = document.createElement("span");
      label.className = "apuSectionLabel";
      label.textContent = matched;
      bubbleEl.appendChild(label);

      const content = line.slice(matched.length).trim();
      if (content) {
        bubbleEl.appendChild(document.createTextNode(" " + content));
        bubbleEl.appendChild(document.createElement("br"));
      }
      continue;
    }

    bubbleEl.appendChild(document.createTextNode(line));
    if (i < lines.length - 1) bubbleEl.appendChild(document.createElement("br"));
  }
}

function textOfItem(item){
  if (!item) return "";
  if (item.title && item.summary) return `${item.id ? item.id + " — " : ""}${item.title}: ${item.summary}`;
  if (item.title) return `${item.id ? item.id + " — " : ""}${item.title}`;
  return item.text || item.question || item.meaning || item.signal || "";
}


function formatItemLine(item){
  const text = textOfItem(item);
  if (!text) return "";
  return `- ${text}`;
}

function formatSection(title, items){
  if (!Array.isArray(items) || !items.length) return "";
  return [
    title.toUpperCase(),
    ...items.map(formatItemLine).filter(Boolean)
  ].join("\n");
}

function formatNotepadSnapshot(caseState){
  if (!caseState || typeof caseState !== "object") {
    return "APU NOTEPAD\nZatím žádný pracovní zápis.";
  }

  const info = caseState.case_info || {};
  const cert = caseState.certainty_and_gaps || {};

  const observableDisplay =
    hasItems(info.observable_anchor)
      ? info.observable_anchor
      : (info.teacher_interpretation_labels || []).map(x => ({
          text: `⚠️ ${x.text || x.label || x.meaning || ""}`,
          status: x.status || "needs_clarification"
        }));

  const caseInfoParts = [
    formatSection("Pozorovaný projev", observableDisplay),
    formatSection("Potřeba učitele", info.pedagogical_need),
    formatSection("Kontext situace", info.context),
    formatSection("Rodič / škola", info.parent_school_difference),
    formatSection("Četnost / intenzita / trend", info.trend_intensity),
  ].filter(x => String(x || "").trim()).join("\n\n");

  const parts = [
    `APU NOTEPAD`,
    `case: ${caseState.case_id || currentCaseId || "—"} · date: ${fmtDateOnly(caseState.created_at || caseState.updated_at)}`,
    "",
    caseInfoParts ? `CASE INFO\n\n${caseInfoParts}` : "",
    formatSection("Pracovní hypotézy", caseState.working_hypotheses),
    formatSection("Co chybí pro zpřesnění", cert.missing_for_disambiguation),
    formatSection("Obecné možnosti podpory", caseState.general_support_options),
    formatSection("Co zkusit", caseState.what_to_try),
    formatSection("Bezpečnost", caseState.safety_notes),
  ].filter(x => String(x || "").trim());

  return parts.join("\n\n");
}

function miniDev(meta){
  const pipe = meta?.pipeline || {};
  const routing = meta?.routing || {};
  const iq = pipe.input_quality || {};
  const flags = Array.isArray(pipe.validation?.flags) ? pipe.validation.flags : [];

  return [
    `mode: ${routing.output_mode || pipe.output_mode || "—"}`,
    `confidence: ${iq.overall_confidence?.level || pipe.confidence || "—"}`,
    `specificity: ${iq.specificity?.level || "—"} / ${iq.specificity?.score ?? "—"}`,
    `blocks: ${codesInline(pipe.blocks)}`,
    `zones: ${codesInline(pipe.zones)}`,
    `flags: ${flags.join(", ") || "—"}`,
  ].join("\n");
}

async function copyTextToClipboard(text, btn){
  try {
    await navigator.clipboard.writeText(text);
    if (btn) {
      const old = btn.textContent;
      btn.textContent = "✓";
      setTimeout(() => { btn.textContent = old; }, 1000);
    }
  } catch {
    if (btn) {
      const old = btn.textContent;
      btn.textContent = "!";
      setTimeout(() => { btn.textContent = old; }, 1000);
    }
  }
}

function formatSessionCopy(){
  const parts = [
    `APU SESSION`,
    `case: ${currentCaseId || "—"}`,
    `turns: ${sessionTurns.length}`,
  ];

  for (const turn of sessionTurns) {
    parts.push(
      "",
      "────────────────────────",
      `TURN ${turn.n}`,
      "",
      "USER:",
      turn.user || "",
      "",
      "APU:",
      turn.apu || "",
      "",
      "DEV MINI:",
      turn.dev || "—",
      "",
      "NOTEPAD SNAPSHOT:",
      turn.notepad || "—",
    );
  }

  if (!sessionTurns.length) {
    parts.push("", formatNotepadSnapshot(latestCaseState));
  }

  return parts.join("\n");
}

function renderNotepadSection(root, title, items, opts = {}) {
  if (!Array.isArray(items) || !items.length) return;

  const section = document.createElement("section");
  section.className = "noteSection";

  const h = document.createElement("div");
  h.className = "noteSectionTitle";
  h.textContent = title;
  section.appendChild(h);

  for (const item of items) {
    const box = document.createElement("div");
    box.className = "noteItem" + (opts.safety ? " noteSafety" : "");

    const text = document.createElement("div");
    text.className = opts.question ? "noteText noteQuestion" : "noteText";
    text.textContent = textOfItem(item) || "—";
    box.appendChild(text);

    section.appendChild(box);
  }

  root.appendChild(section);
}

function hasItems(items){
  return Array.isArray(items) && items.length > 0;
}


function fmtDateOnly(value){
  if (!value) return "—";
  return String(value).slice(0, 10);
}

function renderNotepadSubSection(root, title, items){
  if (!Array.isArray(items) || !items.length) return;

  const sub = document.createElement("div");
  sub.className = "noteSubSection";

  const h = document.createElement("div");
  h.className = "noteSubTitle";
  h.textContent = title;
  sub.appendChild(h);

  for (const item of items) {
    const box = document.createElement("div");
    box.className = "noteItem";
    const text = document.createElement("div");
    text.className = "noteText";
    text.textContent = textOfItem(item) || "—";
    box.appendChild(text);
    sub.appendChild(box);
  }

  root.appendChild(sub);
}

function mergeInfoItems(...groups){
  const out = [];
  const seen = new Set();

  for (const group of groups) {
    for (const item of (Array.isArray(group) ? group : [])) {
      const key = textOfItem(item);
      if (!key || seen.has(key)) continue;
      out.push(item);
      seen.add(key);
    }
  }

  return out;
}

function renderCaseInfoSlot(root, icon, title, items){
  const active = hasItems(items);

  const slot = document.createElement("div");
  slot.className = "caseInfoSlot" + (active ? " isActive" : " isEmpty");

  const iconEl = document.createElement("div");
  iconEl.className = "caseInfoIcon";
  iconEl.textContent = icon;
  slot.appendChild(iconEl);

  const body = document.createElement("div");
  body.className = "caseInfoBody";

  const h = document.createElement("div");
  h.className = "caseInfoSlotTitle";
  h.textContent = title;
  body.appendChild(h);

  const content = document.createElement("div");
  content.className = "caseInfoContent";

  if (active) {
    for (const item of items) {
      const line = document.createElement("div");
      line.className = "caseInfoLine";
      line.textContent = textOfItem(item);
      content.appendChild(line);
    }
  } else {
    const empty = document.createElement("div");
    empty.className = "caseInfoEmptyLine";
    empty.textContent = "— zatím nedoplněno";
    content.appendChild(empty);
  }

  body.appendChild(content);
  slot.appendChild(body);
  root.appendChild(slot);
}

function renderCaseInfo(root, info){
  const section = document.createElement("section");
  section.className = "noteSection caseInfoSection";

  const h = document.createElement("div");
  h.className = "noteSectionTitle caseInfoMainTitle";
  h.textContent = "Informace o případu";
  section.appendChild(h);

  const observableDisplay =
    hasItems(info.observable_anchor)
      ? info.observable_anchor
      : (info.teacher_interpretation_labels || []).map(x => ({
          text: `⚠️ ${x.text}`,
          status: x.status || "needs_clarification"
        }));

  renderCaseInfoSlot(
    section,
    "👁",
    "Pozorovatelný projev",
    observableDisplay
  );

  renderCaseInfoSlot(section, "◎", "Potřeba", info.pedagogical_need);

  const contextItems = mergeInfoItems(
    info.context,
    info.parent_school_difference
  );
  renderCaseInfoSlot(section, "👥", "Kontext", contextItems);

  renderCaseInfoSlot(
    section,
    "◴",
    "Intenzita / trend",
    info.trend_intensity
  );

  root.appendChild(section);
}

function renderNotepad(caseState){
  if (!notepadEl) return;
  notepadEl.textContent = "";

  if (!caseState || typeof caseState !== "object") {
    renderCaseInfo(notepadEl, {});
    return;
  }

  if (caseState.case_id) setCaseId(caseState.case_id);
  if (caseIdLabelEl) {
    caseIdLabelEl.textContent = `case: ${caseState.case_id || currentCaseId || "—"} · date: ${fmtDateOnly(caseState.created_at || caseState.updated_at)}`;
  }

  const info = caseState.case_info || {};
  const cert = caseState.certainty_and_gaps || {};

  const hasV3 =
    hasItems(info.observable_anchor) ||
    hasItems(info.teacher_interpretation_labels) ||
    hasItems(info.pedagogical_need) ||
    hasItems(info.context) ||
    hasItems(info.parent_school_difference) ||
    hasItems(info.trend_intensity) ||
    hasItems(caseState.working_hypotheses) ||
    hasItems(cert.most_supported) ||
    hasItems(cert.missing_for_disambiguation) ||
    hasItems(caseState.what_to_try);

  renderCaseInfo(notepadEl, info);

  if (hasV3) {
    renderNotepadSection(notepadEl, "Pracovní hypotézy", caseState.working_hypotheses);

    renderNotepadSection(notepadEl, "Co chybí pro zpřesnění", cert.missing_for_disambiguation);

    renderNotepadSection(notepadEl, "Obecné možnosti podpory", caseState.general_support_options);
    renderNotepadSection(notepadEl, "Co zkusit", caseState.what_to_try);

    renderNotepadSection(notepadEl, "Bezpečnost", caseState.safety_notes, {safety:true});
  } else {
    const core = caseState.case_core || {};
    const understanding = caseState.case_understanding || {};
    const gaps = caseState.case_gaps || {};

    renderNotepadSection(notepadEl, "Co aktuálně víme – projev", core.observable_anchor);
    renderNotepadSection(notepadEl, "Co aktuálně víme – potřeba učitele", core.pedagogical_need);
    renderNotepadSection(notepadEl, "Kontext: kde / kdy", core.context);
    renderNotepadSection(notepadEl, "Pracovní hypotézy", understanding.plain_language_hypotheses);
    renderNotepadSection(notepadEl, "Co je nejisté / chybí", gaps.missing_information);
    renderNotepadSection(notepadEl, "Co zkusit dál", gaps.recommended_next_step);
  }

  if (!notepadEl.childNodes.length) {
    renderCaseInfo(notepadEl, {});
  }
}

function codesInline(items){
  if (!Array.isArray(items) || !items.length) return "—";
  return items.map(x => {
    const code = x.code || "?";
    const role = x.role ? `/${x.role}` : "";
    const conf = x.confidence ? `/${x.confidence}` : "";
    return `${code}${role}${conf}`;
  }).join(", ");
}

function renderDebug(meta, bubbleEl){
  const pipe = meta.pipeline || {};
  const routing = meta.routing || {};
  const tok = meta.tokens || null;
  const iq = pipe.input_quality || {};
  const flags = Array.isArray(pipe.validation?.flags) ? pipe.validation.flags : [];

  const metaEl = document.createElement("div");
  metaEl.className = "meta";

  const details = document.createElement("details");
  details.className = "debugDetails";

  const summary = document.createElement("summary");
  summary.textContent =
    `DEV · ${routing.output_mode || pipe.output_mode || "—"} · conf ${iq.overall_confidence?.level || pipe.confidence || "—"} · flags ${flags.length}`;
  details.appendChild(summary);

  const grid = document.createElement("div");
  grid.className = "debugGrid";
  grid.innerHTML = `
    <div class="debugItem"><strong>intent</strong> ${pipe.intent || "—"}</div>
    <div class="debugItem"><strong>mode</strong> ${routing.output_mode || pipe.output_mode || "—"}</div>
    <div class="debugItem"><strong>conf</strong> ${iq.overall_confidence?.level || pipe.confidence || "—"}</div>
    <div class="debugItem"><strong>specificity</strong> ${iq.specificity?.level || "—"} / ${iq.specificity?.score ?? "—"}</div>
    <div class="debugItem"><strong>blocks</strong> ${codesInline(pipe.blocks)}</div>
    <div class="debugItem"><strong>zones</strong> ${codesInline(pipe.zones)}</div>
  `;
  details.appendChild(grid);

  if (flags.length) {
    const flagLine = document.createElement("div");
    flagLine.className = "debugFlags";
    flagLine.textContent = `flags: ${flags.join(", ")}`;
    details.appendChild(flagLine);
  }

  if (tok) {
    const tokenLine = document.createElement("div");
    tokenLine.className = "debugFlags";
    const cost = typeof tok.est_cost_usd === "number" ? ` · $${tok.est_cost_usd.toFixed(6)}` : "";
    tokenLine.textContent =
      `tokens: in ~${tok.est_input_tokens} · out ~${tok.est_output_tokens} · total ~${tok.est_total_tokens}${cost}`;
    details.appendChild(tokenLine);

    session.est_in_tokens += tok.est_input_tokens || 0;
    session.est_out_tokens += tok.est_output_tokens || 0;
    session.est_total_tokens += tok.est_total_tokens || 0;
    if (typeof tok.est_cost_usd === "number") {
      session.est_cost_usd = (session.est_cost_usd ?? 0) + tok.est_cost_usd;
    }
    updateSessionStats();
  }

  const row = document.createElement("div");
  row.className = "copyRow";

  const btn = document.createElement("button");
  btn.className = "copyBtn";
  btn.type = "button";
  btn.textContent = "copy";
  btn.title = "Zkopírovat odpověď + DEV info";

  btn.addEventListener("click", async () => {
    const text = [
      bubbleEl?.textContent || "",
      "",
      "--- DEV ---",
      details.innerText || ""
    ].join("\n").trim();

    try {
      await navigator.clipboard.writeText(text);
      btn.textContent = "✓";
      setTimeout(() => { btn.textContent = "copy"; }, 1000);
    } catch {
      btn.textContent = "!";
      setTimeout(() => { btn.textContent = "copy"; }, 1000);
    }
  });

  row.appendChild(btn);
  details.appendChild(row);
  metaEl.appendChild(details);

  return metaEl;
}

async function sendMessage(text) {
  const msg = (text ?? "").trim();
  if (!msg) return;

  addMessage("user", msg);
  inputEl.value = "";
  autoGrow();

  const pending = addMessage("assistant", "…", { loading: true });

  try {
    const body = {
      message: msg,
      llm_extraction: Boolean(llmExtractionToggle?.checked)
    };
    if (currentCaseId) body.case_id = currentCaseId;

    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    });

    const data = await res.json().catch(() => ({}));
    const out = data.response ?? data.reply ?? `[HTTP_${res.status}] ${await res.text()}`;

    pending.bubble.classList.remove("loading");
    renderAssistantBubble(pending.bubble, out);

    if (data.case_id) setCaseId(data.case_id);
    if (data.case_state) {
      latestCaseState = data.case_state;
      renderNotepad(data.case_state);
    }

    let devMini = "";
    if (data.meta) {
      pending.content.appendChild(renderDebug(data.meta, pending.bubble));
      devMini = miniDev(data.meta);
    }

    sessionTurns.push({
      n: sessionTurns.length + 1,
      user: msg,
      apu: pending.bubble.textContent || out,
      dev: devMini,
      notepad: formatNotepadSnapshot(latestCaseState),
    });

  } catch (e) {
    pending.bubble.classList.remove("loading");
    pending.bubble.textContent = `[NETWORK_ERROR] ${e?.message || e}`;
  }

  chatEl.scrollTop = chatEl.scrollHeight;
}

function autoGrow(){
  inputEl.style.height = "auto";
  inputEl.style.height = Math.min(inputEl.scrollHeight, 180) + "px";
}

sendBtn.addEventListener("click", () => sendMessage(inputEl.value));

inputEl.addEventListener("input", autoGrow);

inputEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage(inputEl.value);
  }
});

clearBtn.addEventListener("click", async () => {
  try {
    await fetch("/api/session/reset", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({})
    });
  } catch {}

  chatEl.innerHTML = "";
  currentCaseId = null;
  latestCaseState = null;
  sessionTurns = [];
  setCaseId(null);
  renderNotepad(null);
  session = {
    est_in_tokens: 0,
    est_out_tokens: 0,
    est_total_tokens: 0,
    est_cost_usd: null,
  };
  updateSessionStats();
  addMessage("assistant", "Chat vymazán. Začíná nová prázdná session.");
});

personalBtn.addEventListener("click", () => sendMessage("personal"));

if (copyNotepadBtn) {
  copyNotepadBtn.addEventListener("click", () => {
    copyTextToClipboard(formatNotepadSnapshot(latestCaseState), copyNotepadBtn);
  });
}

if (copySessionBtn) {
  copySessionBtn.addEventListener("click", () => {
    copyTextToClipboard(formatSessionCopy(), copySessionBtn);
  });
}


addMessage("assistant", "Ahoj, jsem APU — asistent pro práci s pedagogickou situací. S čím potřebujete pomoci?");
renderNotepad(null);
autoGrow();
updateSessionStats();
