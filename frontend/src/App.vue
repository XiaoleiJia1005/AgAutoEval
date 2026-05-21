<template>
  <div id="app-root">
    <header class="app-header">
      <div class="header-left">
        <router-link to="/" class="logo">
          <span class="logo-dot"></span>
          AgAutoEval
        </router-link>
        <span class="header-badge">SWE-bench Verified</span>
      </div>
      <nav class="header-nav">
        <router-link to="/" class="nav-link">
          <span class="nav-icon">&#9776;</span>
          Runs
        </router-link>
      </nav>
      <div class="header-right">
        <span class="header-metric" v-if="runningCount > 0" title="Running agents">
          <span class="pulse-dot"></span>
          {{ runningCount }} running
        </span>
      </div>
    </header>
    <main class="app-main">
      <router-view />
    </main>
  </div>
</template>

<script>
export default {
  name: 'App',
  computed: {
    runningCount() {
      return 0
    },
  },
}
</script>

<style>
/* ── surface hierarchy ── */
#app-root {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* ── header ── */
.app-header {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 0 28px;
  height: 56px;
  background: rgba(13, 17, 30, 0.85);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  flex-shrink: 0;
  position: sticky;
  top: 0;
  z-index: 50;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.app-header .logo {
  font-size: 17px;
  font-weight: 700;
  color: #e1e4e8;
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 8px;
  letter-spacing: -0.2px;
}
.logo-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: #58a6ff;
  box-shadow: 0 0 10px rgba(88, 166, 255, 0.5);
  display: inline-block;
}
.header-badge {
  font-size: 11px;
  padding: 3px 10px;
  border-radius: 10px;
  background: rgba(88, 166, 255, 0.1);
  color: #58a6ff;
  border: 1px solid rgba(88, 166, 255, 0.2);
  font-weight: 500;
}
.header-nav {
  display: flex;
  gap: 4px;
  flex: 1;
}
.nav-link {
  color: #8b949e;
  text-decoration: none;
  font-size: 13px;
  padding: 6px 14px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.15s;
}
.nav-link:hover {
  color: #e1e4e8;
  background: rgba(255, 255, 255, 0.05);
}
.nav-link.router-link-exact-active {
  color: #e1e4e8;
  background: rgba(255, 255, 255, 0.08);
}
.nav-icon {
  font-size: 12px;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.header-metric {
  font-size: 12px;
  color: #8b949e;
  display: flex;
  align-items: center;
  gap: 6px;
}
.pulse-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #3fb950;
  display: inline-block;
  animation: pulse 1.8s ease-in-out infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(1.3); }
}

/* ── main area ── */
.app-main {
  flex: 1;
  padding: 28px 32px;
  max-width: 1500px;
  width: 100%;
  margin: 0 auto;
}

/* ── shared table ── */
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
th {
  text-align: left;
  padding: 10px 14px;
  color: #8b949e;
  font-weight: 600;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  white-space: nowrap;
}
td {
  padding: 10px 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  vertical-align: middle;
}
tr {
  transition: background 0.15s, border-color 0.15s;
}
tr:hover td {
  background: rgba(255, 255, 255, 0.04);
}
tr:hover {
  border-left: 3px solid rgba(88, 166, 255, 0.6);
}

/* ── shared card ── */
.card {
  background: rgba(22, 27, 40, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 14px;
  padding: 24px;
  margin-bottom: 16px;
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}

/* ── surface panel ── */
.panel {
  background: rgba(22, 27, 40, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 20px;
}

/* ── badges ── */
.badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.2px;
}
.badge-green { background: rgba(63, 185, 80, 0.15); color: #3fb950; border: 1px solid rgba(63, 185, 80, 0.25); }
.badge-red  { background: rgba(248, 81, 73, 0.15); color: #f85149; border: 1px solid rgba(248, 81, 73, 0.25); }
.badge-gray { background: rgba(139, 148, 158, 0.1); color: #8b949e; border: 1px solid rgba(139, 148, 158, 0.15); }
.badge-blue { background: rgba(88, 166, 255, 0.12); color: #58a6ff; border: 1px solid rgba(88, 166, 255, 0.2); }
.badge-yellow { background: rgba(210, 153, 34, 0.15); color: #d29922; border: 1px solid rgba(210, 153, 34, 0.25); }

/* ── links ── */
.link {
  color: #58a6ff;
  text-decoration: none;
  transition: color 0.15s;
}
.link:hover { color: #79c0ff; }

.mono {
  font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', monospace;
  font-size: 12px;
}

/* ── headings ── */
h2 {
  font-size: 22px;
  margin-bottom: 8px;
  font-weight: 700;
  letter-spacing: -0.3px;
}
h3 {
  font-size: 15px;
  margin-bottom: 12px;
  font-weight: 600;
}

/* ── progress bar ── */
.progress-bar {
  height: 6px;
  border-radius: 3px;
  background: rgba(255, 255, 255, 0.06);
  overflow: hidden;
  min-width: 80px;
}
.progress-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.3s ease;
}
.progress-fill.green { background: linear-gradient(90deg, #238636, #3fb950); }
.progress-fill.yellow { background: linear-gradient(90deg, #9e6a03, #d29922); }
.progress-fill.red { background: linear-gradient(90deg, #da3633, #f85149); }
.progress-fill.gray { background: #30363d; }

/* ── status indicators ── */
.status-dot {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
}
.status-dot::before {
  content: '';
  width: 7px;
  height: 7px;
  border-radius: 50%;
  display: inline-block;
}
.status-done::before { background: #3fb950; }
.status-running::before { background: #3fb950; animation: pulse 1.8s ease-in-out infinite; }
.status-failed::before { background: #f85149; }
.status-pending::before { background: #8b949e; }

/* ── kpi card ── */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 14px;
  margin-bottom: 24px;
}
.kpi-card {
  background: rgba(22, 27, 40, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 14px;
  padding: 20px 24px;
  backdrop-filter: blur(8px);
  transition: all 0.2s;
}
.kpi-card:hover {
  border-color: rgba(255, 255, 255, 0.12);
  transform: translateY(-1px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}
.kpi-label {
  font-size: 11px;
  color: #8b949e;
  text-transform: uppercase;
  letter-spacing: 0.6px;
  margin-bottom: 8px;
  font-weight: 600;
}
.kpi-value {
  font-size: 30px;
  font-weight: 700;
  letter-spacing: -0.5px;
  line-height: 1;
}
.kpi-value.green { color: #3fb950; }
.kpi-value.blue { color: #58a6ff; }
.kpi-value.yellow { color: #d29922; }
.kpi-sub {
  font-size: 12px;
  color: #8b949e;
  margin-top: 6px;
}

/* ── filter chips ── */
.filter-chips {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-bottom: 4px;
}
.chip {
  font-size: 11px;
  padding: 4px 12px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.06);
  color: #8b949e;
  cursor: pointer;
  transition: all 0.15s;
}
.chip:hover {
  border-color: rgba(88, 166, 255, 0.3);
  color: #c9d1d9;
}
.chip.active {
  background: rgba(88, 166, 255, 0.12);
  border-color: rgba(88, 166, 255, 0.3);
  color: #58a6ff;
}

/* ── divider ── */
.section-divider {
  border: 0;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  margin: 20px 0;
}

/* ── sortable col ── */
.sortable {
  cursor: pointer;
  user-select: none;
}
.sortable:hover {
  color: #58a6ff;
}
.sort-arrow {
  font-size: 10px;
}
</style>
