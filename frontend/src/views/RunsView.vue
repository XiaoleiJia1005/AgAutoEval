<template>
  <div>
    <!-- KPI Summary Cards -->
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-label">Overall Accuracy</div>
        <div class="kpi-value" :class="kpiAccuracyColor">{{ kpiAccuracy }}</div>
        <div class="kpi-sub">{{ kpiResolved }} / {{ kpiTotal }} resolved</div>
        <div class="kpi-trend" :class="kpiAccuracyTrend >= 0 ? 'up' : 'down'" v-if="runs.length >= 2">
          <span>{{ kpiAccuracyTrend >= 0 ? '&#9650;' : '&#9660;' }}</span>
          {{ Math.abs(kpiAccuracyTrend).toFixed(1) }}% vs previous
        </div>
        <div class="sparkline" v-if="accuracyHistory.length > 1">
          <div
            v-for="(v, i) in accuracyHistory"
            :key="i"
            class="sparkline-bar"
            :style="{ height: Math.max(4, v * 28) + 'px', opacity: 0.4 + v * 0.6 }"
          ></div>
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Total Runs</div>
        <div class="kpi-value blue">{{ runs.length }}</div>
        <div class="kpi-sub">across {{ modelCount }} models</div>
        <div class="kpi-trend up" v-if="completedCount > 0">
          <span>&#9650;</span> {{ completedCount }} completed
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Avg Duration</div>
        <div class="kpi-value blue">{{ kpiAvgDuration }}</div>
        <div class="kpi-sub">per evaluation run</div>
        <div class="kpi-trend up" v-if="fastestRun">
          <span>&#9650;</span> fastest: {{ formatDuration(fastestRun) }}
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">完成率</div>
        <div class="kpi-value" :class="completionRateColor" style="font-size: 28px;">{{ completionRate }}</div>
        <div class="kpi-sub">{{ completedCount }} / {{ runs.length }} runs</div>
        <div class="kpi-trend up" v-if="runningCount > 0">
          <span>&#9650;</span> {{ runningCount }} running
        </div>
      </div>
    </div>

    <!-- Page header -->
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px;">
      <div>
        <h2 style="margin-bottom: 2px;">Evaluation Runs</h2>
        <p style="color: #8b949e; font-size: 12px;">
          {{ baseDir }}
        </p>
      </div>
      <div style="display: flex; align-items: center; gap: 12px;">
        <span v-if="runs.length" style="color: #8b949e; font-size: 12px;">
          {{ filteredRuns.length }} of {{ runs.length }} runs
        </span>
        <button class="launch-btn-inline" @click="openLaunch">
          <span>+</span> Launch Run
        </button>
      </div>
    </div>

    <!-- Quick filter chips -->
    <div v-if="runs.length" class="filter-chips">
      <button :class="['chip', { active: !filterAgent && !filterProvider && !filterModel && !quickFilter && !statusFilter }]" @click="clearFilters">All</button>
      <button :class="['chip', { active: statusFilter === 'running' }]" @click="statusFilter = statusFilter === 'running' ? '' : 'running'">
        <span class="mini-pulse"></span> Running
      </button>
      <button :class="['chip', { active: statusFilter === 'completed' }]" @click="statusFilter = statusFilter === 'completed' ? '' : 'completed'">Completed</button>
      <button :class="['chip', { active: quickFilter === 'high' }]" @click="quickFilter = quickFilter === 'high' ? '' : 'high'">High Accuracy</button>
      <span style="color: #30363d; margin: 0 4px;">|</span>
      <button
        v-for="a in agentOptions.slice(0, 3)"
        :key="'a-'+a"
        :class="['chip', { active: filterAgent === a }]"
        @click="filterAgent = filterAgent === a ? '' : a"
      >{{ a }}</button>
    </div>

    <!-- Dropdown filters -->
    <div v-if="runs.length" style="display: flex; gap: 10px; flex-wrap: wrap; align-items: center; margin-bottom: 16px;">
      <select v-model="filterAgent" class="filter-select">
        <option value="">All Agents</option>
        <option v-for="a in agentOptions" :key="a" :value="a">{{ a }}</option>
      </select>
      <select v-model="filterProvider" class="filter-select">
        <option value="">All Providers</option>
        <option v-for="p in providerOptions" :key="p" :value="p">{{ p }}</option>
      </select>
      <select v-model="filterModel" class="filter-select">
        <option value="">All Models</option>
        <option v-for="m in modelOptions" :key="m" :value="m">{{ m }}</option>
      </select>
    </div>

    <div v-if="loading" class="panel" style="color: #8b949e; text-align: center; padding: 40px;">Loading...</div>
    <div v-else-if="error" class="card" style="color: #f85149;">{{ error }}</div>

    <div v-else-if="filteredRuns.length" class="panel" style="padding: 0; overflow: hidden;">
      <table>
        <thead>
          <tr>
            <th style="width: 130px;">Status</th>
            <th>Run ID</th>
            <th>Agent</th>
            <th>Provider</th>
            <th>Model</th>
            <th>Benchmark</th>
            <th>Resolved</th>
            <th class="sortable" @click="toggleSort">
              Accuracy
              <span class="sort-arrow">{{ sortDir === 'desc' ? ' ▼' : sortDir === 'asc' ? ' ▲' : '' }}</span>
            </th>
            <th>Duration</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="run in sortedRuns" :key="run.run_id">
            <td>
              <span :class="['status-dot', statusInfo(run).cls]" style="font-size: 11px;">
                {{ statusInfo(run).label }}
              </span>
            </td>
            <td>
              <router-link :to="`/run/${run.run_id}`" class="link mono">
                {{ run.run_id }}
              </router-link>
            </td>
            <td>
              <span class="badge" :class="agentBadge(run.agent_type)" :title="agentLabel(run.agent_type)">
                {{ run.agent_type }}
              </span>
            </td>
            <td>
              <span class="provider-cell" v-if="run.provider">
                <span class="provider-icon-svg" v-html="providerSvg(run.provider)"></span>
                <span class="badge" :class="providerBadge(run.provider)">{{ run.provider }}</span>
              </span>
              <span v-else class="badge badge-gray">-</span>
            </td>
            <td class="mono" style="max-width: 180px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" :title="run.model">
              {{ run.model || '-' }}
            </td>
            <td>
              <span style="font-size: 11px; color: #8b949e;">SWE-bench Verified</span>
            </td>
            <td>
              <span v-if="run.resolved != null" style="font-variant-numeric: tabular-nums; font-size: 12px;">
                <strong style="color: #3fb950;">{{ run.resolved }}</strong>
                <span style="color: #8b949e;"> / {{ run.total }}</span>
              </span>
              <span v-else style="color: #8b949e;">-</span>
            </td>
            <td style="min-width: 160px;">
              <div v-if="run.accuracy != null" style="display: flex; align-items: center; gap: 8px;">
                <div class="progress-bar" style="flex: 1;">
                  <div
                    class="progress-fill"
                    :class="accuracyColor(run.accuracy)"
                    :style="{ width: Math.max(4, (run.accuracy * 100)) + '%' }"
                  ></div>
                </div>
                <span :class="['mono', 'accuracy-text', accuracyColor(run.accuracy)]" style="font-size: 11px; white-space: nowrap; min-width: 44px; text-align: right;">
                  {{ (run.accuracy * 100).toFixed(1) }}%
                </span>
              </div>
              <span v-else style="color: #8b949e; font-size: 12px;">-</span>
            </td>
            <td style="white-space: nowrap; font-size: 12px;">{{ formatDuration(run.total_duration) }}</td>
            <td>
              <router-link :to="`/run/${run.run_id}`" class="link" style="font-size: 12px; font-weight: 500;">View &rarr;</router-link>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-else class="panel" style="color: #8b949e; text-align: center; padding: 48px 24px;">
      <template v-if="runs.length">No runs match the selected filters.</template>
      <template v-else>
        <p style="font-size: 15px; margin-bottom: 8px;">No evaluation runs found.</p>
        <p style="font-size: 13px;">Run <code class="mono" style="background: rgba(255,255,255,0.05); padding: 2px 6px; border-radius: 4px;">python -m agautoeval config.yaml</code> to get started.</p>
      </template>
    </div>
  </div>
</template>

<script>
import { getRuns } from '../api.js'
import { formatDuration, agentBadge, providerBadge, accuracyColor, providerIcon, providerSvg, agentLabel, statusInfo } from '../utils.js'

export default {
  name: 'RunsView',
  data() {
    return {
      runs: [],
      baseDir: '',
      loading: true,
      error: '',
      filterAgent: '',
      filterProvider: '',
      filterModel: '',
      quickFilter: '',
      statusFilter: '',
      sortDir: 'desc',
    }
  },
  computed: {
    agentOptions() {
      return [...new Set(this.runs.map(r => r.agent_type).filter(Boolean))].sort()
    },
    providerOptions() {
      return [...new Set(this.runs.map(r => r.provider).filter(Boolean))].sort()
    },
    modelOptions() {
      return [...new Set(this.runs.map(r => r.model).filter(Boolean))].sort()
    },
    modelCount() {
      return this.modelOptions.length
    },
    completedCount() {
      return this.runs.filter(r => r.accuracy != null && r.total > 0).length
    },
    filteredRuns() {
      let result = this.runs
      if (this.filterAgent) result = result.filter(r => r.agent_type === this.filterAgent)
      if (this.filterProvider) result = result.filter(r => r.provider === this.filterProvider)
      if (this.filterModel) result = result.filter(r => r.model === this.filterModel)
      if (this.statusFilter === 'running') result = result.filter(r => r.total == null && r.instance_count > 0)
      if (this.statusFilter === 'completed') result = result.filter(r => r.accuracy != null)
      if (this.quickFilter === 'high') result = result.filter(r => r.accuracy != null && r.accuracy >= 0.5)
      return result
    },
    sortedRuns() {
      if (!this.sortDir) return this.filteredRuns
      return [...this.filteredRuns].sort((a, b) => {
        const va = a.accuracy ?? -1
        const vb = b.accuracy ?? -1
        return this.sortDir === 'desc' ? vb - va : va - vb
      })
    },
    // KPI computed
    kpiAccuracy() {
      const withAcc = this.runs.filter(r => r.accuracy != null)
      if (!withAcc.length) return '-'
      const avg = withAcc.reduce((s, r) => s + r.accuracy, 0) / withAcc.length
      return (avg * 100).toFixed(1) + '%'
    },
    kpiAccuracyColor() {
      const withAcc = this.runs.filter(r => r.accuracy != null)
      if (!withAcc.length) return ''
      const avg = withAcc.reduce((s, r) => s + r.accuracy, 0) / withAcc.length
      return accuracyColor(avg)
    },
    kpiAccuracyTrend() {
      const withAcc = this.runs.filter(r => r.accuracy != null)
      if (withAcc.length < 2) return 0
      const latest = withAcc[0].accuracy
      const prev = withAcc[1].accuracy
      return (latest - prev) * 100
    },
    kpiResolved() {
      return this.runs.reduce((s, r) => s + (r.resolved ?? 0), 0)
    },
    kpiTotal() {
      return this.runs.reduce((s, r) => s + (r.total ?? 0), 0)
    },
    kpiAvgDuration() {
      const withDur = this.runs.filter(r => r.total_duration > 0)
      if (!withDur.length) return '-'
      const avg = withDur.reduce((s, r) => s + (r.total_duration ?? 0), 0) / withDur.length
      return formatDuration(avg)
    },
    fastestRun() {
      const withDur = this.runs.filter(r => r.total_duration > 0)
      if (!withDur.length) return null
      return Math.min(...withDur.map(r => r.total_duration))
    },
    completionRate() {
      if (!this.runs.length) return '-'
      const pct = (this.completedCount / this.runs.length) * 100
      return pct.toFixed(1) + '%'
    },
    completionRateColor() {
      if (!this.runs.length) return ''
      const pct = this.completedCount / this.runs.length
      return accuracyColor(pct)
    },
    runningCount() {
      return this.runs.filter(r => r.total == null && r.instance_count > 0).length
    },
    accuracyHistory() {
      return this.runs.filter(r => r.accuracy != null).slice(0, 10).map(r => r.accuracy).reverse()
    },
  },
  async created() {
    try {
      const data = await getRuns()
      this.runs = data.runs
      this.baseDir = data.base_dir
    } catch (e) {
      this.error = `Failed to load runs: ${e.message}`
    } finally {
      this.loading = false
    }
  },
  methods: {
    formatDuration,
    agentBadge,
    providerBadge,
    accuracyColor,
    providerIcon,
    agentLabel,
    providerSvg,
    statusInfo,
    toggleSort() {
      if (this.sortDir === 'desc') this.sortDir = 'asc'
      else if (this.sortDir === 'asc') this.sortDir = ''
      else this.sortDir = 'desc'
    },
    clearFilters() {
      this.filterAgent = ''
      this.filterProvider = ''
      this.filterModel = ''
      this.quickFilter = ''
      this.statusFilter = ''
    },
    openLaunch() {
      window.dispatchEvent(new CustomEvent('agautoeval:open-launch'))
    },
  },
}
</script>

<style scoped>
.filter-select {
  background: rgba(22, 27, 40, 0.8);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: #c9d1d9;
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 12px;
  cursor: pointer;
  min-width: 140px;
  transition: border-color 0.15s;
}
.filter-select:focus {
  outline: none;
  border-color: rgba(88, 166, 255, 0.4);
}
.accuracy-text.green { color: #3fb950; }
.accuracy-text.yellow { color: #d29922; }
.accuracy-text.red { color: #f85149; }

.provider-cell {
  display: flex;
  align-items: center;
  gap: 7px;
}
.provider-icon-svg {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.launch-btn-inline {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 7px 16px;
  border-radius: 8px;
  background: rgba(88, 166, 255, 0.12);
  border: 1px solid rgba(88, 166, 255, 0.25);
  color: #58a6ff;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
}
.launch-btn-inline:hover {
  background: rgba(88, 166, 255, 0.2);
  border-color: rgba(88, 166, 255, 0.4);
  box-shadow: 0 0 12px rgba(88, 166, 255, 0.15);
}

.mini-pulse {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #3fb950;
  display: inline-block;
  animation: pulse 1.8s ease-in-out infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(1.3); }
}
</style>
