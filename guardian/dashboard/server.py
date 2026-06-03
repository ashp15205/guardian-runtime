"""
Guardian Dashboard Server
===========================
Serves a local dark-mode web dashboard at http://localhost:3001

  GET /          → full HTML dashboard page
  GET /api/stats → aggregated stats from ~/.guardian/logs/
  GET /api/events → last N log entries
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

GUARDIAN_DIR = Path.home() / ".guardian"
LOGS_DIR = GUARDIAN_DIR / "logs"

# ---------------------------------------------------------------------------
# Log reader
# ---------------------------------------------------------------------------

def _read_all_logs(max_days: int = 7) -> list[dict]:
    """Read up to max_days of JSONL log files, newest first."""
    if not LOGS_DIR.exists():
        return []
    files = sorted(LOGS_DIR.glob("*.jsonl"), reverse=True)[:max_days]
    records: list[dict] = []
    for f in files:
        try:
            for line in f.read_text(encoding="utf-8").strip().splitlines():
                if line.strip():
                    records.append(json.loads(line))
        except Exception:
            pass
    # newest first
    records.sort(key=lambda r: r.get("timestamp", ""), reverse=True)
    return records


def _compute_stats(records: list[dict]) -> dict:
    """Compute aggregated stats from log records."""
    total = len(records)
    blocked = sum(1 for r in records if r.get("event") == "blocked")
    allowed = sum(1 for r in records if r.get("event") == "allowed")

    total_cost = 0.0
    total_input_tokens = 0
    total_output_tokens = 0
    violation_types: Counter = Counter()

    for r in records:
        meta = r.get("metadata", {})
        total_cost += meta.get("estimated_cost_usd", 0.0)
        total_input_tokens += meta.get("input_tokens", 0)
        total_output_tokens += meta.get("output_tokens", 0)
        for v in r.get("violations", []):
            violation_types[v.get("type", "unknown")] += 1

    return {
        "total_requests": total,
        "blocked": blocked,
        "allowed": allowed,
        "block_rate_pct": round((blocked / total * 100) if total > 0 else 0, 1),
        "total_cost_usd": round(total_cost, 6),
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
        "violations_by_type": dict(violation_types.most_common()),
    }


# ---------------------------------------------------------------------------
# Dashboard HTML (single-file, dark mode, auto-refresh)
# ---------------------------------------------------------------------------

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Guardian Dashboard</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root {
      --bg: #0a0a0f;
      --bg2: #10101a;
      --bg3: #1a1a28;
      --border: rgba(255,255,255,.07);
      --text: #e8e8f0;
      --muted: #6b7280;
      --accent: #00ff9d;
      --red: #ff4d6d;
      --yellow: #fbbf24;
      --mono: 'JetBrains Mono', monospace;
    }
    body { background: var(--bg); color: var(--text); font-family: 'Inter', sans-serif; min-height: 100vh; }

    /* NAV */
    nav {
      border-bottom: 1px solid var(--border);
      padding: 1rem 2rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    .nav-brand { display: flex; align-items: center; gap: .6rem; font-weight: 700; font-size: 1rem; }
    .nav-dot { width: 8px; height: 8px; background: var(--accent); border-radius: 50%; animation: pulse 2s infinite; }
    @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.3} }
    .nav-status { font-family: var(--mono); font-size: .75rem; color: var(--accent); }

    /* MAIN LAYOUT */
    main { max-width: 1200px; margin: 0 auto; padding: 2rem; }
    h1 { font-size: 1.5rem; margin-bottom: .3rem; }
    .subtitle { color: var(--muted); font-size: .85rem; margin-bottom: 2rem; font-family: var(--mono); }

    /* STATS GRID */
    .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1px; background: var(--border); border: 1px solid var(--border); margin-bottom: 2rem; }
    .stat-card { background: var(--bg2); padding: 1.4rem 1.5rem; position: relative; }
    .stat-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px; background: var(--accent); opacity: .5; }
    .stat-card.danger::before { background: var(--red); }
    .stat-card.warn::before { background: var(--yellow); }
    .stat-label { font-size: .7rem; color: var(--muted); text-transform: uppercase; letter-spacing: .08em; margin-bottom: .5rem; font-family: var(--mono); }
    .stat-value { font-size: 2rem; font-weight: 700; line-height: 1; }
    .stat-sub { font-size: .75rem; color: var(--muted); margin-top: .3rem; font-family: var(--mono); }

    /* SECTION */
    .section-title { font-size: .7rem; text-transform: uppercase; letter-spacing: .1em; color: var(--muted); margin-bottom: 1rem; font-family: var(--mono); }

    /* VIOLATIONS BAR */
    .viol-row { display: flex; align-items: center; gap: 1rem; margin-bottom: .6rem; }
    .viol-label { font-family: var(--mono); font-size: .78rem; color: var(--text); width: 120px; flex-shrink: 0; }
    .viol-bar-wrap { flex: 1; height: 6px; background: var(--bg3); border-radius: 3px; overflow: hidden; }
    .viol-bar { height: 100%; background: var(--red); border-radius: 3px; transition: width .5s ease; }
    .viol-count { font-family: var(--mono); font-size: .75rem; color: var(--muted); width: 30px; text-align: right; }

    /* EVENTS TABLE */
    .events-wrap { background: var(--bg2); border: 1px solid var(--border); overflow: hidden; }
    table { width: 100%; border-collapse: collapse; font-size: .8rem; }
    thead th { padding: .8rem 1rem; text-align: left; font-family: var(--mono); font-size: .7rem; color: var(--muted); text-transform: uppercase; letter-spacing: .05em; border-bottom: 1px solid var(--border); background: var(--bg3); }
    tbody tr { border-bottom: 1px solid var(--border); transition: background .15s; }
    tbody tr:hover { background: var(--bg3); }
    tbody td { padding: .75rem 1rem; vertical-align: middle; }
    .badge { display: inline-flex; align-items: center; gap: .3rem; padding: .2rem .5rem; border-radius: 4px; font-family: var(--mono); font-size: .7rem; font-weight: 600; }
    .badge.blocked { background: rgba(255,77,109,.12); color: var(--red); }
    .badge.allowed { background: rgba(0,255,157,.08); color: var(--accent); }
    .ts { font-family: var(--mono); font-size: .72rem; color: var(--muted); }
    .vtype { font-family: var(--mono); font-size: .72rem; color: var(--yellow); }
    .agent { font-family: var(--mono); font-size: .72rem; }
    .cost { font-family: var(--mono); font-size: .72rem; color: var(--muted); }

    /* FOOTER */
    .footer { text-align: center; padding: 2rem; font-family: var(--mono); font-size: .72rem; color: var(--muted); }
    .refresh-dot { display: inline-block; width: 6px; height: 6px; background: var(--accent); border-radius: 50%; margin-right: .4rem; animation: pulse 2s infinite; }
  </style>
</head>
<body>
  <nav>
    <div class="nav-brand">
      <div class="nav-dot"></div>
      ⛨ Guardian Dashboard
    </div>
    <div class="nav-status" id="last-refresh">Loading...</div>
  </nav>

  <main>
    <h1>Local AI Firewall</h1>
    <p class="subtitle" id="log-path">Reading from ~/.guardian/logs/ &nbsp;·&nbsp; auto-refreshes every 5s</p>

    <!-- Stats -->
    <div class="stats-grid" id="stats-grid">
      <div class="stat-card"><div class="stat-label">Total Requests</div><div class="stat-value" id="s-total">—</div></div>
      <div class="stat-card danger"><div class="stat-label">Blocked</div><div class="stat-value" id="s-blocked">—</div><div class="stat-sub" id="s-rate">—</div></div>
      <div class="stat-card"><div class="stat-label">Allowed</div><div class="stat-value" id="s-allowed">—</div></div>
      <div class="stat-card warn"><div class="stat-label">Total Cost</div><div class="stat-value" id="s-cost">—</div><div class="stat-sub">USD (last 7 days)</div></div>
      <div class="stat-card"><div class="stat-label">Input Tokens</div><div class="stat-value" id="s-in-tok">—</div></div>
      <div class="stat-card"><div class="stat-label">Output Tokens</div><div class="stat-value" id="s-out-tok">—</div></div>
    </div>

    <!-- Violations by type -->
    <div style="margin-bottom: 2rem;">
      <div class="section-title">Violations by Type</div>
      <div id="violations-chart">
        <p style="color: var(--muted); font-size: .82rem; font-family: var(--mono);">No violations yet.</p>
      </div>
    </div>

    <!-- Events table -->
    <div style="margin-bottom: 2rem;">
      <div class="section-title">Recent Requests (last 50)</div>
      <div class="events-wrap">
        <table>
          <thead>
            <tr>
              <th>Time</th>
              <th>Status</th>
              <th>Agent</th>
              <th>Violations</th>
              <th>Cost</th>
              <th>Tokens In/Out</th>
            </tr>
          </thead>
          <tbody id="events-body">
            <tr><td colspan="6" style="text-align:center; color: var(--muted); padding: 2rem; font-family: var(--mono);">Loading...</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </main>

  <div class="footer">
    <span class="refresh-dot"></span>
    Guardian Runtime · Local-only · No data leaves your machine
  </div>

  <script>
    const fmt = (n) => n >= 1000 ? (n/1000).toFixed(1)+'k' : String(n);
    const fmtCost = (n) => '$' + (n < 0.001 ? n.toFixed(6) : n.toFixed(4));
    const fmtTime = (ts) => {
      try {
        const d = new Date(ts);
        return d.toLocaleTimeString([], {hour:'2-digit', minute:'2-digit', second:'2-digit'});
      } catch { return ts; }
    };

    async function loadStats() {
      try {
        const r = await fetch('/api/stats');
        const d = await r.json();
        document.getElementById('s-total').textContent = fmt(d.total_requests);
        document.getElementById('s-blocked').textContent = fmt(d.blocked);
        document.getElementById('s-rate').textContent = d.block_rate_pct + '% block rate';
        document.getElementById('s-allowed').textContent = fmt(d.allowed);
        document.getElementById('s-cost').textContent = fmtCost(d.total_cost_usd);
        document.getElementById('s-in-tok').textContent = fmt(d.total_input_tokens);
        document.getElementById('s-out-tok').textContent = fmt(d.total_output_tokens);

        // Violations chart
        const chart = document.getElementById('violations-chart');
        const vtypes = d.violations_by_type || {};
        const keys = Object.keys(vtypes);
        if (keys.length === 0) {
          chart.innerHTML = '<p style="color: var(--muted); font-size: .82rem; font-family: var(--mono);">No violations yet.</p>';
        } else {
          const max = Math.max(...Object.values(vtypes));
          chart.innerHTML = keys.map(k => `
            <div class="viol-row">
              <div class="viol-label">${k}</div>
              <div class="viol-bar-wrap"><div class="viol-bar" style="width:${Math.round(vtypes[k]/max*100)}%"></div></div>
              <div class="viol-count">${vtypes[k]}</div>
            </div>`).join('');
        }
      } catch(e) {
        console.error('stats error', e);
      }
    }

    async function loadEvents() {
      try {
        const r = await fetch('/api/events?limit=50');
        const events = await r.json();
        const tbody = document.getElementById('events-body');
        if (events.length === 0) {
          tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; color: var(--muted); padding: 2rem; font-family: var(--mono);">No events yet. Run your agent.</td></tr>';
          return;
        }
        tbody.innerHTML = events.map(e => {
          const isBlocked = e.event === 'blocked';
          const viols = (e.violations || []).map(v => v.type).join(', ') || '—';
          const meta = e.metadata || {};
          const cost = meta.estimated_cost_usd != null ? fmtCost(meta.estimated_cost_usd) : '—';
          const tokens = (meta.input_tokens != null) ? `${fmt(meta.input_tokens)} / ${fmt(meta.output_tokens||0)}` : '—';
          return `<tr>
            <td class="ts">${fmtTime(e.timestamp)}</td>
            <td><span class="badge ${isBlocked ? 'blocked' : 'allowed'}">${isBlocked ? '⛔ BLOCKED' : '✓ ALLOWED'}</span></td>
            <td class="agent">${e.agent_id || 'default'}</td>
            <td class="vtype">${viols}</td>
            <td class="cost">${cost}</td>
            <td class="cost">${tokens}</td>
          </tr>`;
        }).join('');
      } catch(e) {
        console.error('events error', e);
      }
    }

    function refresh() {
      loadStats();
      loadEvents();
      document.getElementById('last-refresh').textContent =
        'Last updated: ' + new Date().toLocaleTimeString();
    }

    refresh();
    setInterval(refresh, 5000);
  </script>
</body>
</html>"""

# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

def create_dashboard_app() -> FastAPI:
    app = FastAPI(title="Guardian Dashboard", docs_url=None, redoc_url=None)
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

    @app.get("/", response_class=HTMLResponse)
    async def index():
        return HTMLResponse(content=DASHBOARD_HTML)

    @app.get("/api/stats")
    async def api_stats():
        records = _read_all_logs()
        return JSONResponse(content=_compute_stats(records))

    @app.get("/api/events")
    async def api_events(limit: int = 50):
        records = _read_all_logs()
        return JSONResponse(content=records[:limit])

    return app
