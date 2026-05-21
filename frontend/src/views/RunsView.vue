<template>
  <div>
    <!-- KPI Summary Cards -->
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-label">Overall Accuracy</div>
        <div class="kpi-value" :class="kpiAccuracyColor">{{ kpiAccuracy }}</div>
        <div class="kpi-sub">{{ kpiResolved }} / {{ kpiTotal }} resolved</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Total Runs</div>
        <div class="kpi-value blue">{{ runs.length }}</div>
        <div class="kpi-sub">across {{ modelCount }} models</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Avg Duration</div>
        <div class="kpi-value blue">{{ kpiAvgDuration }}</div>
        <div class="kpi-sub">per evaluation run</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Top Model</div>
        <div class="kpi-value green" style="font-size: 20px;">{{ topModel }}</div>
        <div class="kpi-sub">{{ topModelAccuracy }} accuracy</div>
      </div>
    </div>

    <!-- Page header -->
    <div style="display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 16px;">
      <div>
        <h2 style="margin-bottom: 4px;">Evaluation Runs</h2>
        <p style="color: #8b949e; font-size: 13px;">
          {{ baseDir }}
        </p>
      </div>
      <span v-if="runs.length" style="color: #8b949e; font-size: 12px;">
        {{ filteredRuns.length }} of {{ runs.length }} runs
      </span>
    </div>

    <!-- Quick filter chips -->
    <div v-if="runs.length" class="filter-chips">
      <button :class="['chip', { active: !filterAgent && !filterProvider && !filterModel && !quickFilter }]" @click="clearFilters">All</button>
      <button :class="['chip', { active: quickFilter === 'high' }]" @click="quickFilter = quickFilter === 'high' ? '' : 'high'">High Accuracy</button>
      <button :class="['chip', { active: quickFilter === 'resolved' }]" @click="quickFilter = quickFilter === 'resolved' ? '' : 'resolved'">Most Resolved</button>
      <span style="color: #30363d; margin: 0 6px;">|</span>
      <button
        v-for="a in agentOptions.slice(0, 3)"
        :key="'a-'+a"
        :class="['chip', { active: filterAgent === a }]"
        @click="filterAgent = filterAgent === a ? '' : a"
      >{{ a }}</button>
      <span style="color: #30363d; margin: 0 6px;">|</span>
      <button
        v-for="p in providerOptions.slice(0, 4)"
        :key="'p-'+p"
        :class="['chip', { active: filterProvider === p }]"
        @click="filterProvider = filterProvider === p ? '' : p"
      >{{ providerIcon(p) }} {{ p }}</button>
    </div>

    <!-- Dropdown filters -->
    <div v-if="runs.length" style="display: flex; gap: 10px; flex-wrap: wrap; align-items: center; margin-bottom: 16px;">
      <select v-model="filterAgent" class="filter-select">
        <option value="">All Agents</option>
        <option v-for="a in agentOptions" :key="a" :value="a">{{ agentLabel(a) }}</option>
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
            <th style="width: 50px;"></th>
            <th>Run ID</th>
            <th>Agent</th>
            <th>Provider</th>
            <th>Model</th>
            <th>Instances</th>
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
            <td style="padding-right: 0;">
              <span :class="['status-dot', statusInfo(run).cls]"></span>
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
              <span class="badge" :class="providerBadge(run.provider)">
                {{ providerIcon(run.provider) }} {{ run.provider }}
              </span>
            </td>
            <td class="mono" style="max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" :title="run.model">
              {{ run.model || '-' }}
            </td>
            <td>{{ run.instance_count }}</td>
            <td>
              <span v-if="run.resolved != null" style="font-variant-numeric: tabular-nums;">
                <strong style="color: #3fb950;">{{ run.resolved }}</strong>
                <span style="color: #8b949e;"> / {{ run.total }}</span>
              </span>
              <span v-else>-</span>
            </td>
            <td>
              <div v-if="run.accuracy != null" style="display: flex; align-items: center; gap: 10px;">
                <div class="progress-bar" style="flex: 1;">
                  <div
                    class="progress-fill"
                    :class="accuracyColor(run.accuracy)"
                    :style="{ width: (run.accuracy * 100).toFixed(1) + '%' }"
                  ></div>
                </div>
                <span :class="['mono', 'accuracy-text', accuracyColor(run.accuracy)]" style="font-size: 12px; white-space: nowrap; min-width: 48px; text-align: right;">
                  {{ (run.accuracy * 100).toFixed(1) }}%
                </span>
              </div>
              <span v-else style="color: #8b949e;">-</span>
            </td>
            <td style="white-space: nowrap;">{{ formatDuration(run.total_duration) }}</td>
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
import { formatDuration, agentBadge, providerBadge, accuracyColor, providerIcon, agentLabel, statusInfo } from '../utils.js'

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
    filteredRuns() {
      let result = this.runs
      if (this.filterAgent) result = result.filter(r => r.agent_type === this.filterAgent)
      if (this.filterProvider) result = result.filter(r => r.provider === this.filterProvider)
      if (this.filterModel) result = result.filter(r => r.model === this.filterModel)
      if (this.quickFilter === 'high') result = result.filter(r => r.accuracy != null && r.accuracy >= 0.5)
      if (this.quickFilter === 'resolved') {
        result = [...result].sort((a, b) => (b.resolved ?? 0) - (a.resolved ?? 0)).slice(0, 5)
      }
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
    topModel() {
      const best = [...this.runs].filter(r => r.accuracy != null).sort((a, b) => b.accuracy - a.accuracy)[0]
      return best ? (best.model || '?') : '-'
    },
    topModelAccuracy() {
      const best = [...this.runs].filter(r => r.accuracy != null).sort((a, b) => b.accuracy - a.accuracy)[0]
      return best ? (best.accuracy * 100).toFixed(1) + '%' : '-'
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
</style>
