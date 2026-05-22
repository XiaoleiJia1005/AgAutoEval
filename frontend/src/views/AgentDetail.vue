<template>
  <div>
    <div style="margin-bottom: 20px;">
      <router-link to="/agents" class="link" style="font-size: 13px;">&larr; All agents</router-link>
    </div>

    <div v-if="loading" class="panel" style="color: #8b949e; text-align: center; padding: 40px;">Loading agent profile...</div>
    <div v-else-if="error" class="card" style="color: #f85149;">{{ error }}</div>

    <template v-else>
      <!-- Agent Header -->
      <div class="agent-header">
        <div class="agent-header-left">
          <div class="agent-avatar-lg" :class="agentBadgeClass(agent.id)">
            <span>{{ agent.id.charAt(0).toUpperCase() }}</span>
          </div>
          <div>
            <h2 style="margin-bottom: 4px;">{{ agent.label }}</h2>
            <div class="header-sub">
              <span class="badge" :class="agentBadgeClass(agent.id)">{{ agent.id }}</span>
              <span v-if="agent.latestVersion" class="mono" style="font-size: 11px; color: #8b949e;">v{{ agent.latestVersion }}</span>
              <span class="status-dot status-done" style="font-size: 11px;">Active</span>
            </div>
          </div>
        </div>
        <div style="display: flex; gap: 10px;">
          <button class="compare-btn" @click="openCompare">
            <span v-html="dimIcon('compare')" style="display: flex; align-items: center;"></span>
            Compare
          </button>
          <button class="launch-btn-inline" @click="openLaunch">
            <span>+</span> Run Evaluation
          </button>
        </div>
      </div>

      <p class="agent-desc-lg">{{ agent.desc }}</p>

      <!-- Capabilities -->
      <div class="capability-tags" style="margin-bottom: 24px;">
        <span v-for="c in agent.capabilities" :key="c" class="cap-tag">{{ c }}</span>
      </div>

      <!-- Overview KPI -->
      <div class="kpi-grid">
        <div class="kpi-card">
          <div class="kpi-label">Latest Accuracy</div>
          <div class="kpi-value" :class="accuracyColor(agent.latestAccuracy / 100)" style="font-size: 28px;">
            {{ agent.latestAccuracy != null ? agent.latestAccuracy.toFixed(1) + '%' : '-' }}
          </div>
          <div class="kpi-trend" :class="trendDirection" v-if="Math.abs(accuracyTrend) > 0.1">
            <span>{{ accuracyTrend >= 0 ? '&#9650;' : '&#9660;' }}</span>
            {{ Math.abs(accuracyTrend).toFixed(1) }}pp
          </div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Best Accuracy</div>
          <div class="kpi-value green" style="font-size: 28px;">
            {{ agent.bestAccuracy != null ? agent.bestAccuracy.toFixed(1) + '%' : '-' }}
          </div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Avg Duration</div>
          <div class="kpi-value blue" style="font-size: 28px;">{{ avgDuration }}</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Total Runs</div>
          <div class="kpi-value blue" style="font-size: 28px;">{{ agentRuns.length }}</div>
          <div class="kpi-sub">across {{ benchmarkCount }} benchmarks</div>
        </div>
      </div>

      <!-- Benchmark History Chart -->
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px;">
        <div class="panel">
          <div class="panel-header-row">
            <h3>Benchmark History</h3>
            <div style="display: flex; gap: 6px;">
              <select v-model="historyBenchmark" class="mini-select" @change="updateHistory">
                <option v-for="b in benchmarks" :key="b.id" :value="b.id">{{ b.label }}</option>
              </select>
              <select v-model="historyModel" class="mini-select" @change="updateHistory">
                <option value="">All models</option>
                <option v-for="m in availableModels" :key="m" :value="m">{{ m }}</option>
              </select>
            </div>
          </div>
          <p style="color: #8b949e; font-size: 12px; margin-bottom: 6px;">
            {{ agent.label }}<span v-if="historyModel"> using {{ historyModel }}</span> on {{ selectedBenchmarkLabel }}
          </p>
          <div style="display: flex; gap: 8px; margin-bottom: 10px;">
            <button v-for="mode in historyModes" :key="mode" :class="['toggle-btn', { active: historyMode === mode }]" @click="historyMode = mode; updateHistory()">{{ mode }}</button>
          </div>
          <div class="chart-area" v-if="chartData.length > 0">
            <div class="bar-chart">
              <div v-for="(d, i) in chartData" :key="i" class="bar-col">
                <div class="bar-val" style="font-size: 10px; color: #8b949e; margin-bottom: 2px;">{{ (d.accuracy * 100).toFixed(0) }}%</div>
                <div class="bar-wrap">
                  <div
                    class="bar-fill"
                    :class="accuracyColor(d.accuracy)"
                    :style="{ height: Math.max(4, d.accuracy * 100) + '%' }"
                  ></div>
                </div>
                <div class="bar-label mono" style="font-size: 9px; color: #484f58; margin-top: 4px;">{{ d.label }}</div>
              </div>
            </div>
          </div>
          <div v-else style="color: #8b949e; font-size: 13px; padding: 20px 0;">Not enough data for history chart.</div>
        </div>

        <!-- Version History -->
        <div class="panel">
          <h3>Version History</h3>
          <table v-if="versionRows.length" style="margin-top: 8px;">
            <thead>
              <tr>
                <th>Version</th>
                <th>Accuracy</th>
                <th>Runs</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="v in versionRows" :key="v.version">
                <td class="mono">{{ v.version || 'unknown' }}</td>
                <td>
                  <span v-if="v.accuracy != null" :class="accuracyColor(v.accuracy)" style="font-weight: 600;">
                    {{ (v.accuracy * 100).toFixed(1) }}%
                  </span>
                  <span v-else>-</span>
                </td>
                <td>{{ v.runCount }}</td>
              </tr>
            </tbody>
          </table>
          <div v-else style="color: #8b949e; font-size: 12px; padding: 20px 0;">No version data available. Add version to agent config.</div>
        </div>
      </div>

      <!-- Cross-Benchmark + Runtime Config -->
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px;">
        <!-- Cross-Benchmark -->
        <div class="panel">
          <div class="panel-header-row">
            <h3>Cross-Benchmark Performance</h3>
            <div style="display: flex; gap: 6px;">
              <select v-model="crossModel" class="mini-select" @change="updateCrossBenchmark">
                <option value="">All models</option>
                <option v-for="m in availableModels" :key="m" :value="m">{{ m }}</option>
              </select>
              <select v-model="crossVersion" class="mini-select" @change="updateCrossBenchmark">
                <option value="">All versions</option>
                <option v-for="v in availableVersions" :key="v" :value="v">{{ v || 'unknown' }}</option>
              </select>
            </div>
          </div>
          <p style="color: #8b949e; font-size: 12px; margin-bottom: 10px;">
            {{ agent.label }}<span v-if="crossVersion"> v{{ crossVersion }}</span><span v-if="crossModel"> on {{ crossModel }}</span>
          </p>
          <div class="chart-area" v-if="crossBenchmark.length > 0">
            <div class="bar-chart">
              <div v-for="(b, i) in crossBenchmark" :key="i" class="bar-col">
                <div class="bar-val" style="font-size: 10px; color: #8b949e; margin-bottom: 2px;">
                  {{ b.accuracy != null ? (b.accuracy * 100).toFixed(0) + '%' : '-' }}
                </div>
                <div class="bar-wrap">
                  <div
                    class="bar-fill"
                    :class="accuracyColor(b.accuracy)"
                    :style="{ height: Math.max(4, (b.accuracy || 0) * 100) + '%' }"
                  ></div>
                </div>
                <div class="bar-label mono" style="font-size: 9px; color: #484f58; margin-top: 4px; text-align: center; line-height: 1.2;">
                  {{ b.nameShort }}
                </div>
              </div>
            </div>
          </div>
          <div v-else style="color: #8b949e; font-size: 12px; padding: 20px 0;">Run on more benchmarks to see cross-benchmark data.</div>
        </div>

        <!-- Runtime Config -->
        <div class="panel">
          <h3>Runtime Configuration</h3>
          <div class="config-display" v-if="hasRuntimeConfig">
            <div class="config-row">
              <span class="config-key">Agent Type</span>
              <span class="config-val">{{ agent.id }}</span>
            </div>
            <div class="config-row">
              <span class="config-key">Tool Policy</span>
              <span class="config-val">{{ toolPolicy || 'sandboxed' }}</span>
            </div>
            <div class="config-row">
              <span class="config-key">Timeout</span>
              <span class="config-val">{{ defaultTimeout }}s</span>
            </div>
            <div class="config-row">
              <span class="config-key">Sandbox</span>
              <span class="config-val">Docker</span>
            </div>
          </div>
          <div v-else style="color: #8b949e; font-size: 12px; padding: 20px 0;">No runtime config available. Add details to agent config.</div>
        </div>
      </div>

      <!-- Installation & Usage -->
      <div class="panel" style="margin-bottom: 20px;">
        <h3>Installation &amp; Usage</h3>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
          <div>
            <div class="install-label">Install</div>
            <pre class="code-block" v-if="agentDef.defaults && agentDef.defaults.install_cmd"><code>{{ agentDef.defaults.install_cmd }}</code></pre>
            <pre class="code-block" v-else><code># No install command configured</code></pre>
            <div class="install-label" style="margin-top: 12px;">Usage</div>
            <pre class="code-block" v-if="agentDef.defaults && agentDef.defaults.command"><code>{{ agentDef.defaults.command.replace('{problem_statement}', '"fix failing tests"') }}</code></pre>
            <pre class="code-block" v-else><code># No run command configured</code></pre>
          </div>
          <div>
            <div class="install-label">Required Environment</div>
            <div v-if="Object.keys(agentEnvs).length" class="env-list">
              <div v-for="(v, k) in agentEnvs" :key="k" class="env-row">
                <code class="env-key">{{ k }}</code>
                <span class="env-val">{{ maskSecret(v) }}</span>
              </div>
            </div>
            <div v-else style="color: #8b949e; font-size: 12px; padding: 8px 0;">No environment variables configured.</div>
            <div class="install-label" style="margin-top: 12px;">Sandbox</div>
            <div style="font-size: 12px; color: #c9d1d9; padding: 4px 0;">Docker</div>
            <div class="install-label" style="margin-top: 8px;">Provider</div>
            <div style="font-size: 12px; color: #c9d1d9; padding: 4px 0;">{{ agentDef.provider || firstRunProvider }}</div>
          </div>
        </div>
      </div>

      <!-- Recent Runs -->
      <div class="panel" style="padding: 0; overflow: hidden; margin-bottom: 20px;">
        <div style="padding: 14px 20px; border-bottom: 1px solid rgba(255,255,255,0.05);">
          <h3 style="margin-bottom: 0;">Recent Runs</h3>
        </div>
        <table v-if="recentRuns.length">
          <thead>
            <tr>
              <th>Run ID</th>
              <th>Model</th>
              <th>Accuracy</th>
              <th>Duration</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in recentRuns" :key="r.run_id">
              <td>
                <router-link :to="`/run/${r.run_id}`" class="link mono">
                  {{ r.run_id }}
                </router-link>
              </td>
              <td class="mono" style="font-size: 12px;">{{ r.model || '-' }}</td>
              <td>
                <span v-if="r.accuracy != null" :class="accuracyColor(r.accuracy)" style="font-weight: 600;">
                  {{ (r.accuracy * 100).toFixed(1) }}%
                </span>
                <span v-else>-</span>
              </td>
              <td style="font-size: 12px;">{{ formatDuration(r.total_duration) }}</td>
              <td>
                <router-link :to="`/run/${r.run_id}`" class="link" style="font-size: 12px;">View &rarr;</router-link>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Trace Samples -->
      <div class="panel">
        <h3>Trace Samples</h3>
        <p style="color: #484f58; font-size: 12px;">
          Representative execution traces — fastest solve, best reasoning, longest retry. Enable agent trace recording to populate this section.
        </p>
      </div>
    </template>
  </div>
</template>

<script>
import { getRuns, getAgents } from '../api.js'
import { formatDuration, agentBadge, accuracyColor, dimIcon } from '../utils.js'
import { BENCHMARKS } from '../utils.js'

export default {
  name: 'AgentDetail',
  props: { agentId: String },
  data() {
    return {
      agent: {},
      agentDefs: [],
      agentRuns: [],
      allRuns: [],
      loading: true,
      error: '',
      historyBenchmark: 'swebench-verified',
      historyModel: '',
      historyMode: 'latest',
      crossModel: '',
      crossVersion: '',
    }
  },
  computed: {
    agentDef() {
      return this.agentDefs.find(a => a.type === this.agentId) || {}
    },
    benchmarks() {
      return BENCHMARKS
    },
    historyModes() {
      return ['latest', 'best', 'average']
    },
    selectedBenchmarkLabel() {
      const b = BENCHMARKS.find(b => b.id === this.historyBenchmark)
      return b ? b.label : this.historyBenchmark
    },
    availableModels() {
      const models = new Set()
      for (const r of this.agentRuns) {
        if (r.model) models.add(r.model)
      }
      return [...models].sort()
    },
    availableVersions() {
      const versions = new Set()
      for (const r of this.agentRuns) {
        if (r.agent_version) versions.add(r.agent_version)
      }
      return [...versions].sort().reverse()
    },
    latestAccuracy() {
      const withAcc = this.agentRuns.filter(r => r.accuracy != null)
      return withAcc.length ? withAcc[0].accuracy * 100 : null
    },
    bestAccuracy() {
      const withAcc = this.agentRuns.map(r => r.accuracy).filter(Boolean)
      return withAcc.length ? Math.max(...withAcc) * 100 : null
    },
    avgDuration() {
      const runs = this.filteredRuns()
      return formatDuration(
        runs.reduce((s, r) => s + (r.total_duration || 0), 0) / Math.max(1, runs.length)
      )
    },
    benchmarkCount() {
      return this.allRuns.filter(r => r.dataset_name).length || 1
    },
    accuracyTrend() {
      const accs = this.agentRuns.filter(r => r.accuracy != null)
      if (accs.length < 2) return 0
      return (accs[0].accuracy - accs[1].accuracy) * 100
    },
    trendDirection() {
      return this.accuracyTrend >= 0 ? 'up' : 'down'
    },
    chartData() {
      return this.buildChartData()
    },
    versionRows() {
      const groups = {}
      for (const r of this.agentRuns) {
        const v = r.agent_version || ''
        if (!groups[v]) groups[v] = { accs: [], count: 0 }
        groups[v].count++
        if (r.accuracy != null) groups[v].accs.push(r.accuracy)
      }
      return Object.entries(groups).map(([version, data]) => ({
        version: version || 'unknown',
        accuracy: data.accs.length ? data.accs.reduce((s, a) => s + a, 0) / data.accs.length : null,
        runCount: data.count,
      })).sort((a, b) => b.runCount - a.runCount)
    },
    crossBenchmark() {
      const filtered = this.filterCrossRuns()
      const accs = filtered.filter(r => r.accuracy != null).map(r => r.accuracy)
      return [{
        name: 'SWE-bench Verified',
        nameShort: 'SWE-bench',
        accuracy: accs.length ? accs.reduce((s, a) => s + a, 0) / accs.length : null,
        avgDuration: accs.length ? formatDuration(filtered.filter(r => r.total_duration > 0).reduce((s, r) => s + r.total_duration, 0) / filtered.filter(r => r.total_duration > 0).length || 1) : null,
      }]
    },
    recentRuns() {
      return this.agentRuns.slice(0, 10)
    },
    toolPolicy() {
      return this.agentRuns.find(r => r.agent_tool_policy)?.agent_tool_policy || ''
    },
    defaultTimeout() {
      return this.agentRuns.find(r => r.total_duration > 0) ? 1800 : 1800
    },
    hasRuntimeConfig() {
      return true
    },
    agentEnvs() {
      const envs = {}
      for (const r of this.agentRuns) {
        if (r.envs) {
          for (const [k, v] of Object.entries(r.envs)) {
            envs[k] = v
          }
        }
      }
      return envs
    },
    firstRunProvider() {
      return this.agentRuns.find(r => r.provider)?.provider || '-'
    },
  },
  async created() {
    try {
      const [runsData, agentsData] = await Promise.all([
        getRuns(),
        getAgents(),
      ])
      const allRuns = runsData.runs || []
      this.allRuns = allRuns
      this.agentRuns = allRuns.filter(r => r.agent_type === this.agentId)
      this.agentDefs = agentsData.agents || []

      const def = this.agentDef
      const withAcc = this.agentRuns.filter(r => r.accuracy != null)
      const accuracies = withAcc.map(r => r.accuracy)

      this.agent = {
        id: this.agentId,
        label: def.label || this.agentId,
        desc: def.description || 'No description available.',
        capabilities: def.capabilities || ['tool-use'],
        latestVersion: this.agentRuns[0]?.agent_version || '',
        latestAccuracy: accuracies.length ? accuracies[0] * 100 : null,
        bestAccuracy: accuracies.length ? Math.max(...accuracies) * 100 : null,
      }
    } catch (e) {
      this.error = `Failed to load agent data: ${e.message}`
    } finally {
      this.loading = false
    }
  },
  methods: {
    formatDuration,
    agentBadgeClass(type) {
      return agentBadge(type).replace('badge-', '')
    },
    accuracyColor(acc) {
      return accuracyColor(acc != null ? acc : null)
    },
    dimIcon,
    openLaunch() {
      window.dispatchEvent(new CustomEvent('agautoeval:open-launch'))
    },
    openCompare() {
      window.dispatchEvent(new CustomEvent('agautoeval:open-compare', { detail: { runId: '' } }))
    },
    filteredRuns() {
      let runs = this.agentRuns
      if (this.historyModel) {
        runs = runs.filter(r => r.model === this.historyModel)
      }
      return runs
    },
    buildChartData() {
      let runs = this.filteredRuns().filter(r => r.accuracy != null)
      if (this.historyMode === 'best') {
        const byVersion = {}
        for (const r of runs) {
          const v = r.agent_version || 'unknown'
          if (!byVersion[v] || r.accuracy > byVersion[v].accuracy) byVersion[v] = r
        }
        runs = Object.values(byVersion)
      } else if (this.historyMode === 'average') {
        const byVersion = {}
        for (const r of runs) {
          const v = r.agent_version || 'unknown'
          if (!byVersion[v]) byVersion[v] = { accs: [], run: r }
          byVersion[v].accs.push(r.accuracy)
        }
        runs = Object.values(byVersion).map(g => ({
          ...g.run,
          accuracy: g.accs.reduce((s, a) => s + a, 0) / g.accs.length,
        }))
      }
      return runs.slice(0, 12).reverse().map(r => ({
        accuracy: r.accuracy,
        label: r.run_id ? r.run_id.slice(9, 15).replace('_', '') : '?',
      }))
    },
    filterCrossRuns() {
      let runs = this.agentRuns
      if (this.crossModel) {
        runs = runs.filter(r => r.model === this.crossModel)
      }
      if (this.crossVersion) {
        runs = runs.filter(r => r.agent_version === this.crossVersion)
      }
      return runs
    },
    updateHistory() {
      // Triggered by selector changes — chartData recomputed reactively
    },
    updateCrossBenchmark() {
      // Triggered by selector changes — crossBenchmark recomputed reactively
    },
    maskSecret(val) {
      if (!val) return '-'
      if (val.length <= 8) return '••••'
      return val.slice(0, 4) + '••••' + val.slice(-4)
    },
  },
}
</script>

<style scoped>
.agent-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}
.agent-header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}
.agent-avatar-lg {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: 700;
  flex-shrink: 0;
}
.agent-avatar-lg.green { background: rgba(63, 185, 80, 0.15); color: #3fb950; }
.agent-avatar-lg.blue { background: rgba(88, 166, 255, 0.15); color: #58a6ff; }
.agent-avatar-lg.gray { background: rgba(139, 148, 158, 0.1); color: #8b949e; }
.header-sub {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
  margin-top: 4px;
}
.agent-desc-lg {
  font-size: 14px;
  color: #8b949e;
  line-height: 1.6;
  max-width: 700px;
  margin-bottom: 12px;
}
.capability-tags { display: flex; gap: 6px; flex-wrap: wrap; }
.cap-tag {
  font-size: 11px;
  padding: 3px 10px;
  border-radius: 8px;
  background: rgba(255,255,255,0.05);
  color: #c9d1d9;
  border: 1px solid rgba(255,255,255,0.08);
  font-weight: 500;
}

/* Chart */
.chart-area { padding: 8px 0; }
.bar-chart {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  height: 140px;
}
.bar-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100%;
}
.bar-wrap {
  flex: 1;
  width: 100%;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}
.bar-fill {
  width: 70%;
  max-width: 32px;
  border-radius: 3px 3px 0 0;
  transition: height 0.3s;
  min-height: 4px;
}
.bar-fill.green { background: linear-gradient(180deg, #3fb950, rgba(63, 185, 80, 0.3)); }
.bar-fill.yellow { background: linear-gradient(180deg, #d29922, rgba(210, 153, 34, 0.3)); }
.bar-fill.red { background: linear-gradient(180deg, #f85149, rgba(248, 81, 73, 0.3)); }

/* Runtime config display */
.config-display { display: flex; flex-direction: column; gap: 0; }
.config-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid rgba(255,255,255,0.04);
}
.config-key { font-size: 12px; color: #8b949e; }
.config-val { font-size: 13px; color: #e1e4e8; font-weight: 500; }

/* Buttons */
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
}
.launch-btn-inline:hover {
  background: rgba(88, 166, 255, 0.2);
  border-color: rgba(88, 166, 255, 0.4);
}
.compare-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 7px 16px;
  border-radius: 8px;
  background: rgba(139, 148, 158, 0.08);
  border: 1px solid rgba(139, 148, 158, 0.15);
  color: #c9d1d9;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
}
.compare-btn:hover {
  border-color: rgba(88, 166, 255, 0.3);
  background: rgba(88, 166, 255, 0.08);
  color: #58a6ff;
}
.compare-btn :deep(svg) { stroke: currentColor; }

/* Panel header row */
.panel-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 12px;
}
.panel-header-row h3 {
  margin-bottom: 0;
  flex-shrink: 0;
}

/* Mini selectors */
.mini-select {
  padding: 4px 8px;
  border-radius: 6px;
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.08);
  color: #8b949e;
  font-size: 11px;
  cursor: pointer;
  max-width: 160px;
}
.mini-select:focus {
  outline: none;
  border-color: rgba(88, 166, 255, 0.3);
  color: #e1e4e8;
}

/* Toggle buttons */
.toggle-btn {
  padding: 3px 10px;
  border-radius: 5px;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.06);
  color: #8b949e;
  font-size: 10px;
  font-weight: 500;
  cursor: pointer;
  text-transform: capitalize;
  transition: all 0.15s;
}
.toggle-btn:hover {
  border-color: rgba(255,255,255,0.12);
  color: #c9d1d9;
}
.toggle-btn.active {
  background: rgba(88, 166, 255, 0.12);
  border-color: rgba(88, 166, 255, 0.3);
  color: #58a6ff;
}

/* Installation & Usage */
.install-label {
  font-size: 10px;
  color: #8b949e;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 600;
  margin-bottom: 6px;
}
.code-block {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 8px;
  padding: 10px 14px;
  font-size: 12px;
  color: #c9d1d9;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
}
.code-block code {
  font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', monospace;
  font-size: 12px;
  background: none;
  padding: 0;
}
.env-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.env-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 3px 0;
}
.env-key {
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-size: 11px;
  color: #58a6ff;
  background: rgba(88, 166, 255, 0.06);
  padding: 2px 6px;
  border-radius: 4px;
}
.env-val {
  font-size: 11px;
  color: #8b949e;
  font-family: 'SF Mono', 'Fira Code', monospace;
}
</style>
