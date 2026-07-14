"use strict";

async function api(path, options) {
  const response = await fetch(path, options);
  if (!response.ok) throw new Error(`${path} -> ${response.status}`);
  return response.json();
}

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function badge(value) {
  return el("span", `badge ${value}`, value);
}

function card(label, value) {
  const node = el("div", "card");
  node.appendChild(el("div", "value", value));
  node.appendChild(el("div", "label", label));
  return node;
}

async function loadScorecard() {
  const report = await api("/scorecard");
  const card_ = report.scorecard;
  const cards = document.getElementById("scorecard");
  cards.innerHTML = "";
  cards.appendChild(card("Detection", `${Math.round(card_.detection_rate * 100)}%`));
  cards.appendChild(card("Resilience", `${Math.round(card_.resilience_rate * 100)}%`));
  cards.appendChild(card("Mean TTD", `${card_.mean_time_to_detect_ticks}t`));
  cards.appendChild(card("Alert loss", `${Math.round(card_.alert_loss_rate * 100)}%`));
  cards.appendChild(card("Findings", `${card_.findings.length}`));

  const findings = document.getElementById("findings");
  findings.innerHTML = "";
  for (const finding of card_.findings) {
    const node = el("div", `finding ${finding.severity}`);
    node.appendChild(badge(finding.severity));
    node.append(` ${finding.experiment}: ${finding.summary}`);
    findings.appendChild(node);
  }
  return report;
}

function renderDetail(result) {
  const detail = document.getElementById("detail");
  detail.innerHTML = "";
  const head = el("div");
  head.appendChild(badge(result.verdict));
  head.append(
    ` ${result.experiment} — fault ${result.fault}, ` +
      `${result.detected ? `detected in ${result.time_to_detect_ticks} tick(s)` : "not detected"}, ` +
      `${result.alerts_lost} alert(s) lost`
  );
  detail.appendChild(head);
  if (result.reasons.length) detail.appendChild(el("p", "hint", result.reasons.join("; ")));

  const table = el("table");
  const thead = el("tr");
  for (const h of ["Control", "Kind", "Tick", "Alerted", "Delivered"]) thead.appendChild(el("th", null, h));
  table.appendChild(thead);
  for (const d of result.detections) {
    const row = el("tr");
    row.appendChild(el("td", null, d.control));
    row.appendChild(el("td", null, d.kind));
    row.appendChild(el("td", null, String(d.at_tick)));
    row.appendChild(el("td", null, d.alerted ? "yes" : "no"));
    row.appendChild(el("td", null, d.alert_delivered ? "yes" : "no"));
    table.appendChild(row);
  }
  detail.appendChild(table);
}

async function loadExperiments(report) {
  const data = await api("/experiments");
  const verdicts = {};
  for (const r of report.results) verdicts[r.experiment] = r.verdict;
  const list = document.getElementById("experiments");
  list.innerHTML = "";
  for (const experiment of data.experiments) {
    const cardEl = el("button", "experiment");
    cardEl.type = "button";
    const title = el("div", "title");
    title.appendChild(el("span", null, experiment.title));
    if (verdicts[experiment.id]) title.appendChild(badge(verdicts[experiment.id]));
    cardEl.appendChild(title);
    cardEl.appendChild(el("div", "fault", `${experiment.fault} @ ${experiment.component}`));
    cardEl.addEventListener("click", async () => {
      renderDetail(await api(`/experiments/${experiment.id}/run`, { method: "POST" }));
    });
    list.appendChild(cardEl);
  }
}

async function loadSystem() {
  const system = await api("/system");
  document.getElementById("system-meta").textContent =
    `${system.name} — ${system.components.length} components, ${system.controls.length} controls`;
}

async function main() {
  const report = await loadScorecard();
  await Promise.all([loadExperiments(report), loadSystem()]);
}

main().catch((error) => {
  document.getElementById("subtitle").textContent = `Failed to load: ${error.message}`;
});
