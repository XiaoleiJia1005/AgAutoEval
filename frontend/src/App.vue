<template>
  <div id="app-root">
    <header class="app-header">
      <div class="header-left">
        <router-link to="/" class="logo">
          <span class="logo-dot"></span>
          AgAutoEval
        </router-link>

        <!-- Benchmark selector -->
        <div class="benchmark-select" @click="benchOpen = !benchOpen" v-click-outside="() => benchOpen = false">
          <span class="benchmark-label">{{ currentBenchmark.label }}</span>
          <span class="benchmark-chevron">&#9662;</span>
          <div v-if="benchOpen" class="benchmark-dropdown">
            <div
              v-for="b in benchmarks"
              :key="b.id"
              :class="['benchmark-item', { active: currentBenchmark.id === b.id }]"
              @click.stop="selectBenchmark(b)"
            >
              <div class="benchmark-item-label">{{ b.label }}</div>
              <div class="benchmark-item-meta">{{ b.tasks }} tasks · {{ b.lang }} · {{ b.difficulty }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Main nav -->
      <nav class="header-nav">
        <router-link to="/" class="nav-link" active-class="active">Runs</router-link>
        <a href="#" class="nav-link disabled">Datasets</a>
        <a href="#" class="nav-link disabled">Agents</a>
        <a href="#" class="nav-link disabled">Leaderboard</a>
      </nav>

      <div class="header-right">
        <span class="header-metric" v-if="runningCount > 0" title="Running agents">
          <span class="pulse-dot"></span>
          {{ runningCount }} running
        </span>
        <button class="launch-btn" @click="showLaunchModal = true">
          <span class="launch-icon">+</span>
          Launch Run
        </button>
      </div>
    </header>

    <main class="app-main">
      <router-view />
    </main>

    <!-- Launch Run Modal -->
    <LaunchRunModal v-if="showLaunchModal" @close="showLaunchModal = false" />

    <!-- Compare Modal -->
    <CompareModal
      v-if="showCompareModal"
      :initialRunId="compareRunId"
      @close="showCompareModal = false"
    />
  </div>
</template>

<script>
import { BENCHMARKS } from './utils.js'
import LaunchRunModal from './components/LaunchRunModal.vue'
import CompareModal from './components/CompareModal.vue'

export default {
  name: 'App',
  components: { LaunchRunModal, CompareModal },
  data() {
    return {
      benchOpen: false,
      showLaunchModal: false,
      showCompareModal: false,
      compareRunId: '',
      currentBenchmark: BENCHMARKS[0],
      benchmarks: BENCHMARKS,
    }
  },
  computed: {
    runningCount() {
      return 0
    },
  },
  directives: {
    'click-outside': {
      mounted(el, binding) {
        el._clickOutside = (e) => {
          if (!(el === e.target || el.contains(e.target))) {
            binding.value()
          }
        }
        document.addEventListener('click', el._clickOutside)
      },
      unmounted(el) {
        document.removeEventListener('click', el._clickOutside)
      },
    },
  },
  mounted() {
    this._openLaunch = () => { this.showLaunchModal = true }
    window.addEventListener('agautoeval:open-launch', this._openLaunch)
    this._openCompare = (e) => {
      this.compareRunId = e.detail?.runId || ''
      this.showCompareModal = true
    }
    window.addEventListener('agautoeval:open-compare', this._openCompare)
  },
  unmounted() {
    window.removeEventListener('agautoeval:open-launch', this._openLaunch)
    window.removeEventListener('agautoeval:open-compare', this._openCompare)
  },
  methods: {
    selectBenchmark(b) {
      this.currentBenchmark = b
      this.benchOpen = false
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
  gap: 16px;
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
  gap: 16px;
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
  flex-shrink: 0;
}
.logo-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: #58a6ff;
  box-shadow: 0 0 10px rgba(88, 166, 255, 0.5);
  display: inline-block;
}

/* ── benchmark selector ── */
.benchmark-select {
  position: relative;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 12px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  cursor: pointer;
  transition: all 0.15s;
  user-select: none;
}
.benchmark-select:hover {
  border-color: rgba(255, 255, 255, 0.15);
  background: rgba(255, 255, 255, 0.06);
}
.benchmark-label {
  font-size: 12px;
  color: #8b949e;
  font-weight: 500;
}
.benchmark-chevron {
  font-size: 10px;
  color: #484f58;
}
.benchmark-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  min-width: 260px;
  background: #161b28;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 6px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5);
  z-index: 100;
}
.benchmark-item {
  padding: 10px 14px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.1s;
}
.benchmark-item:hover {
  background: rgba(255, 255, 255, 0.06);
}
.benchmark-item.active {
  background: rgba(88, 166, 255, 0.1);
}
.benchmark-item-label {
  font-size: 13px;
  color: #e1e4e8;
  font-weight: 500;
}
.benchmark-item-meta {
  font-size: 11px;
  color: #8b949e;
  margin-top: 2px;
}

/* ── nav ── */
.header-nav {
  display: flex;
  gap: 2px;
  flex: 1;
}
.nav-link {
  color: #8b949e;
  text-decoration: none;
  font-size: 13px;
  padding: 6px 14px;
  border-radius: 6px;
  transition: all 0.15s;
  font-weight: 500;
}
.nav-link:hover {
  color: #e1e4e8;
  background: rgba(255, 255, 255, 0.05);
}
.nav-link.active {
  color: #e1e4e8;
  background: rgba(255, 255, 255, 0.08);
}
.nav-link.disabled {
  color: #484f58;
  cursor: default;
}
.nav-link.disabled:hover {
  background: none;
  color: #484f58;
}

/* ── header right ── */
.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
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

/* ── launch button ── */
.launch-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 7px 18px;
  border-radius: 8px;
  background: rgba(88, 166, 255, 0.15);
  border: 1px solid rgba(88, 166, 255, 0.3);
  color: #58a6ff;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
}
.launch-btn:hover {
  background: rgba(88, 166, 255, 0.22);
  border-color: rgba(88, 166, 255, 0.5);
  box-shadow: 0 0 16px rgba(88, 166, 255, 0.2);
}
.launch-icon {
  font-size: 15px;
  font-weight: 700;
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
  font-size: 12px;
}
th {
  text-align: left;
  padding: 8px 12px;
  color: #8b949e;
  font-weight: 600;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  white-space: nowrap;
}
td {
  padding: 7px 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  vertical-align: middle;
}
tr {
  transition: background 0.15s;
}
tr:hover td {
  background: rgba(255, 255, 255, 0.04);
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
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.2px;
}
.badge-green  { background: rgba(63, 185, 80, 0.15); color: #3fb950; border: 1px solid rgba(63, 185, 80, 0.25); }
.badge-red    { background: rgba(248, 81, 73, 0.15); color: #f85149; border: 1px solid rgba(248, 81, 73, 0.25); }
.badge-gray   { background: rgba(139, 148, 158, 0.1); color: #8b949e; border: 1px solid rgba(139, 148, 158, 0.15); }
.badge-blue   { background: rgba(88, 166, 255, 0.12); color: #58a6ff; border: 1px solid rgba(88, 166, 255, 0.2); }
.badge-yellow { background: rgba(210, 153, 34, 0.15); color: #d29922; border: 1px solid rgba(210, 153, 34, 0.25); }
.badge-cyan   { background: rgba(57, 211, 204, 0.12); color: #39d2cc; border: 1px solid rgba(57, 211, 204, 0.2); }
.badge-orange { background: rgba(219, 109, 40, 0.15); color: #db6d28; border: 1px solid rgba(219, 109, 40, 0.25); }

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
.progress-fill.green  { background: linear-gradient(90deg, #238636, #3fb950); }
.progress-fill.yellow { background: linear-gradient(90deg, #9e6a03, #d29922); }
.progress-fill.red    { background: linear-gradient(90deg, #da3633, #f85149); }
.progress-fill.gray   { background: #30363d; }

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
  flex-shrink: 0;
}
.status-done::before         { background: #3fb950; }
.status-running::before      { background: #3fb950; animation: pulse 1.8s ease-in-out infinite; }
.status-provisioning::before { background: #58a6ff; animation: pulse 1.8s ease-in-out infinite; }
.status-evaluating::before   { background: #d29922; animation: pulse 1.8s ease-in-out infinite; }
.status-queued::before       { background: #8b949e; }
.status-failed::before       { background: #f85149; }
.status-timeout::before      { background: #db6d28; }
.status-cancelled::before    { background: #484f58; }

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
  margin-bottom: 6px;
  font-weight: 600;
}
.kpi-value {
  font-size: 30px;
  font-weight: 700;
  letter-spacing: -0.5px;
  line-height: 1;
}
.kpi-value.green  { color: #3fb950; }
.kpi-value.blue   { color: #58a6ff; }
.kpi-value.yellow { color: #d29922; }
.kpi-sub {
  font-size: 12px;
  color: #8b949e;
  margin-top: 6px;
}
.kpi-trend {
  font-size: 11px;
  margin-top: 6px;
  display: flex;
  align-items: center;
  gap: 4px;
}
.kpi-trend.up   { color: #3fb950; }
.kpi-trend.down { color: #f85149; }

/* ── sparkline ── */
.sparkline {
  display: flex;
  align-items: flex-end;
  gap: 2px;
  height: 28px;
  margin-top: 8px;
}
.sparkline-bar {
  flex: 1;
  min-width: 3px;
  border-radius: 1px 1px 0 0;
  background: rgba(88, 166, 255, 0.3);
  transition: height 0.3s;
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
