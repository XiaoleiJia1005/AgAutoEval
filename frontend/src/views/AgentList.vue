<template>
  <div>
    <!-- Page header -->
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 24px;">
      <div>
        <h2 style="margin-bottom: 4px;">Agents</h2>
        <p style="color: #8b949e; font-size: 13px;">Agent Hub — compare capabilities, performance, and evolution</p>
      </div>
      <div style="display: flex; gap: 10px;">
        <button class="compare-btn" @click="showCompare = true" v-if="agents.length >= 2">
          <span v-html="dimIcon('compare')" style="display: flex; align-items: center;"></span>
          Compare Agents
        </button>
        <button class="launch-btn-inline" @click="showAddAgent = true">
          <span>+</span> Add Agent
        </button>
      </div>
    </div>

    <div v-if="loading" class="panel" style="color: #8b949e; text-align: center; padding: 40px;">Loading agents...</div>
    <div v-else-if="error" class="card" style="color: #f85149;">{{ error }}</div>

    <template v-else-if="agents.length">
      <!-- Agent Compare Bar -->
      <div v-if="showCompare" class="compare-bar">
        <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
          <span style="font-size: 13px; font-weight: 600; color: #e1e4e8;">Compare</span>
          <select v-model="compareAgentA" class="inline-select" @change="onCompareAgentChange">
            <option value="">Select agent A...</option>
            <option v-for="a in agents" :key="a.id" :value="a.id" :disabled="a.id === compareAgentB">{{ a.label || a.id }}</option>
          </select>
          <span style="color: #484f58;">vs</span>
          <select v-model="compareAgentB" class="inline-select" @change="onCompareAgentChange">
            <option value="">Select agent B...</option>
            <option v-for="a in agents" :key="a.id" :value="a.id" :disabled="a.id === compareAgentA">{{ a.label || a.id }}</option>
          </select>
          <select v-model="compareBenchmark" class="inline-select">
            <option v-for="b in benchmarks" :key="b.id" :value="b.id">{{ b.label }}</option>
          </select>
          <select v-model="compareModel" class="inline-select">
            <option value="">Any model</option>
            <option v-for="m in availableModels" :key="m" :value="m">{{ m }}</option>
          </select>
          <button class="compare-run-btn" :disabled="!canCompare" @click="runCompare">Run Compare</button>
          <button class="compare-close-btn" @click="showCompare = false">&times;</button>
        </div>
        <!-- Compare Results -->
        <div v-if="compareResult" class="compare-results">
          <div style="display: grid; grid-template-columns: 1fr auto 1fr; gap: 20px; align-items: start;">
            <div class="compare-side-panel">
              <div class="compare-agent-name">{{ compareAgentAData?.label || compareAgentA }}</div>
              <div class="compare-metric-row"><span>Accuracy</span><span class="compare-val" :class="accuracyColor(compareResult.a.accuracy)">{{ compareResult.a.accuracy != null ? (compareResult.a.accuracy * 100).toFixed(1) + '%' : '-' }}</span></div>
              <div class="compare-metric-row"><span>Avg Duration</span><span>{{ compareResult.a.avgDuration || '-' }}</span></div>
              <div class="compare-metric-row"><span>Runs</span><span>{{ compareResult.a.runCount }}</span></div>
              <div class="compare-metric-row"><span>Best Accuracy</span><span :class="accuracyColor(compareResult.a.bestAccuracy)">{{ compareResult.a.bestAccuracy != null ? (compareResult.a.bestAccuracy * 100).toFixed(1) + '%' : '-' }}</span></div>
            </div>
            <div style="text-align: center; color: #484f58; font-size: 20px; font-weight: 600;">vs</div>
            <div class="compare-side-panel">
              <div class="compare-agent-name">{{ compareAgentBData?.label || compareAgentB }}</div>
              <div class="compare-metric-row"><span>Accuracy</span><span class="compare-val" :class="accuracyColor(compareResult.b.accuracy)">{{ compareResult.b.accuracy != null ? (compareResult.b.accuracy * 100).toFixed(1) + '%' : '-' }}</span></div>
              <div class="compare-metric-row"><span>Avg Duration</span><span>{{ compareResult.b.avgDuration || '-' }}</span></div>
              <div class="compare-metric-row"><span>Runs</span><span>{{ compareResult.b.runCount }}</span></div>
              <div class="compare-metric-row"><span>Best Accuracy</span><span :class="accuracyColor(compareResult.b.bestAccuracy)">{{ compareResult.b.bestAccuracy != null ? (compareResult.b.bestAccuracy * 100).toFixed(1) + '%' : '-' }}</span></div>
            </div>
          </div>
        </div>
      </div>

      <div class="agent-grid">
      <div
        v-for="agent in agents"
        :key="agent.id"
        class="agent-card"
      >
        <!-- Header -->
        <div class="agent-card-header">
          <div class="agent-avatar" :class="agentBadgeClass(agent.id)">
            <span>{{ agent.id.charAt(0).toUpperCase() }}</span>
          </div>
          <div style="flex: 1; min-width: 0;">
            <router-link :to="`/agents/${agent.id}`" class="link" style="font-size: 16px; font-weight: 600; color: #e1e4e8;">
              {{ agent.label || agent.id }}
            </router-link>
            <div class="agent-version" v-if="agent.latestVersion">{{ agent.latestVersion }}</div>
          </div>
          <span :class="['status-dot', agent.lastActiveStatus]"></span>
        </div>

        <!-- Description -->
        <div class="agent-desc">{{ agent.desc }}</div>

        <!-- Capabilities -->
        <div class="capability-tags" style="margin-bottom: 14px;">
          <span v-for="c in agent.capabilities" :key="c" class="cap-tag">{{ c }}</span>
        </div>

        <!-- Metrics row -->
        <div class="agent-metrics">
          <div class="agent-metric">
            <div class="agent-metric-label">Latest Accuracy</div>
            <div class="agent-metric-value" :class="accuracyColor(agent.latestAccuracy / 100)">
              {{ agent.latestAccuracy != null ? agent.latestAccuracy.toFixed(1) + '%' : '-' }}
            </div>
          </div>
          <div class="agent-metric">
            <div class="agent-metric-label">Best Accuracy</div>
            <div class="agent-metric-value" :class="accuracyColor(agent.bestAccuracy / 100)">
              {{ agent.bestAccuracy != null ? agent.bestAccuracy.toFixed(1) + '%' : '-' }}
            </div>
          </div>
          <div class="agent-metric">
            <div class="agent-metric-label">Benchmarks</div>
            <div class="agent-metric-value" style="color: #c9d1d9;">{{ agent.benchmarkCount }}</div>
          </div>
          <div class="agent-metric">
            <div class="agent-metric-label">Runs</div>
            <div class="agent-metric-value" style="color: #c9d1d9;">{{ agent.runCount }}</div>
          </div>
        </div>

        <!-- Sparkline -->
        <div class="sparkline" v-if="agent.accuracyHistory && agent.accuracyHistory.length > 1" style="margin-top: 12px;">
          <div
            v-for="(v, i) in agent.accuracyHistory"
            :key="i"
            class="sparkline-bar"
            :style="{ height: Math.max(4, v * 28) + 'px', opacity: 0.4 + v * 0.6 }"
          ></div>
        </div>

        <!-- Footer -->
        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 14px;">
          <span style="font-size: 11px; color: #484f58;">{{ agent.lastActive }}</span>
          <router-link :to="`/agents/${agent.id}`" class="link" style="font-size: 12px; font-weight: 500;">View profile &rarr;</router-link>
        </div>
      </div>
    </div>

    </template>

    <div v-else class="panel" style="color: #8b949e; text-align: center; padding: 48px 24px;">
      <p style="font-size: 15px; margin-bottom: 8px;">No agents found.</p>
      <p style="font-size: 13px;">Run an evaluation to populate agent data.</p>
      <button class="launch-btn-inline" style="margin-top: 16px;" @click="showAddAgent = true">
        <span>+</span> Add Agent
      </button>
    </div>

    <!-- Add Agent Modal -->
    <div v-if="showAddAgent" class="modal-overlay" @click.self="showAddAgent = false">
      <div class="modal-container">
        <div class="modal-header">
          <div>
            <h2 class="modal-title">Add Agent</h2>
            <p class="modal-sub">Register a new agent for evaluation</p>
          </div>
          <button class="modal-close" @click="showAddAgent = false">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">Type <span class="required">*</span></label>
            <input v-model="newAgent.type" class="form-input" placeholder="e.g. opencode, swe_agent, custom" />
            <p class="form-hint">Unique identifier for the agent type</p>
          </div>
          <div class="form-group">
            <label class="form-label">Install Command</label>
            <input v-model="newAgent.install_cmd" class="form-input mono" placeholder="e.g. npm install -g opencode-ai" />
          </div>
          <div class="form-group">
            <label class="form-label">Version Command</label>
            <input v-model="newAgent.version_cmd" class="form-input mono" placeholder="e.g. opencode --version" />
          </div>
          <div class="form-group">
            <label class="form-label">Run Command</label>
            <input v-model="newAgent.run_cmd" class="form-input mono" placeholder="e.g. opencode run --model {model} {problem_statement}" />
            <p class="form-hint">Use {'{'}problem_statement{'}'}, {'{'}model{'}'}, {'{'}provider{'}'} as placeholders</p>
          </div>
          <div class="form-group">
            <label class="form-label">Environment Variables</label>
            <div v-for="(env, i) in newAgent.envs" :key="i" class="kv-row">
              <input v-model="env.key" class="form-input kv-input" placeholder="KEY" />
              <input v-model="env.value" class="form-input kv-input" placeholder="value" />
              <button class="kv-remove" @click="newAgent.envs.splice(i, 1)">&times;</button>
            </div>
            <button class="kv-add" @click="newAgent.envs.push({ key: '', value: '' })">+ Add env var</button>
          </div>
          <div class="form-group">
            <label class="form-label">Persist Directories</label>
            <div v-for="(dir, i) in newAgent.persist_dirs" :key="i" class="kv-row">
              <input v-model="newAgent.persist_dirs[i]" class="form-input" placeholder="e.g. /var/run/docker.sock" />
              <button class="kv-remove" @click="newAgent.persist_dirs.splice(i, 1)">&times;</button>
            </div>
            <button class="kv-add" @click="newAgent.persist_dirs.push('')">+ Add directory</button>
          </div>
        </div>
        <div class="modal-footer">
          <div style="flex: 1;"></div>
          <button class="btn-secondary" @click="showAddAgent = false">Cancel</button>
          <button class="btn-primary" :disabled="!newAgent.type" @click="saveAgent">Save Agent</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { getRuns } from '../api.js'
import { agentBadge, accuracyColor, agentLabel, dimIcon } from '../utils.js'
import { AGENT_TYPES, BENCHMARKS } from '../utils.js'

export default {
  name: 'AgentList',
  data() {
    return {
      agents: [],
      allRuns: [],
      loading: true,
      error: '',
      showCompare: false,
      compareAgentA: '',
      compareAgentB: '',
      compareBenchmark: 'swebench-verified',
      compareModel: '',
      compareResult: null,
      showAddAgent: false,
      newAgent: {
        type: '',
        install_cmd: '',
        version_cmd: '',
        run_cmd: '',
        envs: [],
        persist_dirs: [],
      },
    }
  },
  computed: {
    benchmarks() {
      return BENCHMARKS
    },
    availableModels() {
      const models = new Set()
      for (const r of this.allRuns) {
        if (r.model) models.add(r.model)
      }
      return [...models].sort()
    },
    canCompare() {
      return this.compareAgentA && this.compareAgentB && this.compareAgentA !== this.compareAgentB
    },
    compareAgentAData() {
      return this.agents.find(a => a.id === this.compareAgentA)
    },
    compareAgentBData() {
      return this.agents.find(a => a.id === this.compareAgentB)
    },
  },
  async created() {
    try {
      const data = await getRuns()
      const runs = data.runs || []
      this.allRuns = runs
      this.agents = this.buildAgents(runs)
    } catch (e) {
      this.error = `Failed to load agent data: ${e.message}`
    } finally {
      this.loading = false
    }
  },
  methods: {
    accuracyColor(acc) {
      return accuracyColor(acc != null ? acc / 100 : null)
    },
    dimIcon,
    agentBadgeClass(type) {
      return agentBadge(type).replace('badge-', '')
    },
    buildAgents(runs) {
      const groups = {}
      for (const r of runs) {
        const type = r.agent_type || 'unknown'
        if (!groups[type]) {
          groups[type] = []
        }
        groups[type].push(r)
      }

      const defs = {}
      for (const a of AGENT_TYPES) {
        defs[a.id] = a
      }

      return Object.entries(groups).map(([type, agentRuns]) => {
        const withAcc = agentRuns.filter(r => r.accuracy != null)
        const accuracies = withAcc.map(r => r.accuracy)
        const def = defs[type] || {}
        const lastRun = agentRuns[0]
        const latestVersion = lastRun?.agent_version || ''

        return {
          id: type,
          label: agentLabel(type).includes(type) ? type.charAt(0).toUpperCase() + type.slice(1) : type,
          desc: def.desc || 'No description available.',
          capabilities: def.capabilities || ['tool-use'],
          latestAccuracy: accuracies.length ? (Math.max(...accuracies) * 100) : null,
          bestAccuracy: accuracies.length ? (Math.max(...accuracies) * 100) : null,
          latestVersion,
          benchmarkCount: 1,
          runCount: agentRuns.length,
          lastActive: this.timeAgo(agentRuns[0]?.run_id),
          lastActiveStatus: withAcc.length > 0 ? 'status-done' : 'status-queued',
          accuracyHistory: accuracies.slice(0, 10).reverse(),
          _runs: agentRuns,
        }
      }).sort((a, b) => (b.bestAccuracy || 0) - (a.bestAccuracy || 0))
    },
    timeAgo(runId) {
      if (!runId) return 'unknown'
      const m = runId.match(/^(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})/)
      if (!m) return runId
      const d = new Date(+m[1], +m[2] - 1, +m[3], +m[4], +m[5], +m[6])
      const now = Date.now()
      const diff = now - d.getTime()
      const hours = Math.floor(diff / 3600000)
      if (hours < 1) return 'just now'
      if (hours < 24) return `${hours}h ago`
      const days = Math.floor(hours / 24)
      return `${days}d ago`
    },
    onCompareAgentChange() {
      this.compareResult = null
    },
    runCompare() {
      if (!this.canCompare) return
      const aRuns = this.filterCompareRuns(this.compareAgentA)
      const bRuns = this.filterCompareRuns(this.compareAgentB)
      const aAccs = aRuns.filter(r => r.accuracy != null).map(r => r.accuracy)
      const bAccs = bRuns.filter(r => r.accuracy != null).map(r => r.accuracy)
      const aDurs = aRuns.filter(r => r.total_duration > 0)
      const bDurs = bRuns.filter(r => r.total_duration > 0)
      this.compareResult = {
        a: {
          accuracy: aAccs.length ? aAccs.reduce((s, a) => s + a, 0) / aAccs.length : null,
          bestAccuracy: aAccs.length ? Math.max(...aAccs) : null,
          avgDuration: aDurs.length ? this.formatDuration(aDurs.reduce((s, r) => s + r.total_duration, 0) / aDurs.length) : null,
          runCount: aRuns.length,
        },
        b: {
          accuracy: bAccs.length ? bAccs.reduce((s, a) => s + a, 0) / bAccs.length : null,
          bestAccuracy: bAccs.length ? Math.max(...bAccs) : null,
          avgDuration: bDurs.length ? this.formatDuration(bDurs.reduce((s, r) => s + r.total_duration, 0) / bDurs.length) : null,
          runCount: bRuns.length,
        },
      }
    },
    filterCompareRuns(agentId) {
      let runs = this.allRuns.filter(r => r.agent_type === agentId)
      if (this.compareModel) {
        runs = runs.filter(r => r.model === this.compareModel)
      }
      return runs
    },
    formatDuration(s) {
      if (!s || s <= 0) return '-'
      if (s < 60) return `${s.toFixed(0)}s`
      if (s < 3600) return `${Math.floor(s / 60)}m ${Math.floor(s % 60)}s`
      return `${Math.floor(s / 3600)}h ${Math.floor((s % 3600) / 60)}m`
    },
    saveAgent() {
      if (!this.newAgent.type) return
      const cleanEnvs = {}
      for (const e of this.newAgent.envs) {
        if (e.key) cleanEnvs[e.key] = e.value
      }
      const agentDef = {
        id: this.newAgent.type.toLowerCase().replace(/\s+/g, '_'),
        label: this.newAgent.type,
        desc: `Custom agent: ${this.newAgent.type}`,
        capabilities: ['tool-use'],
        install_cmd: this.newAgent.install_cmd,
        version_cmd: this.newAgent.version_cmd,
        run_cmd: this.newAgent.run_cmd,
        envs: cleanEnvs,
        persist_dirs: this.newAgent.persist_dirs.filter(Boolean),
      }
      // Add to in-memory agents list (would persist to backend in production)
      this.agents.push({
        id: agentDef.id,
        label: agentDef.label,
        desc: agentDef.desc,
        capabilities: agentDef.capabilities,
        latestAccuracy: null,
        bestAccuracy: null,
        latestVersion: '',
        benchmarkCount: 0,
        runCount: 0,
        lastActive: 'just now',
        lastActiveStatus: 'status-queued',
        accuracyHistory: [],
        _runs: [],
      })
      this.showAddAgent = false
      this.newAgent = { type: '', install_cmd: '', version_cmd: '', run_cmd: '', envs: [], persist_dirs: [] }
    },
  },
}
</script>

<style scoped>
.agent-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}
.agent-card {
  background: rgba(22, 27, 40, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 16px;
  padding: 24px;
  transition: all 0.2s;
}
.agent-card:hover {
  border-color: rgba(88, 166, 255, 0.2);
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.3);
}
.agent-card-header {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 12px;
}
.agent-avatar {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: 700;
  flex-shrink: 0;
}
.agent-avatar.green { background: rgba(63, 185, 80, 0.15); color: #3fb950; }
.agent-avatar.blue { background: rgba(88, 166, 255, 0.15); color: #58a6ff; }
.agent-avatar.gray { background: rgba(139, 148, 158, 0.1); color: #8b949e; }
.agent-version {
  font-size: 11px;
  color: #8b949e;
  margin-top: 2px;
  font-family: 'SF Mono', 'Fira Code', monospace;
}
.agent-desc {
  font-size: 13px;
  color: #8b949e;
  line-height: 1.5;
  margin-bottom: 10px;
}
.capability-tags { display: flex; gap: 4px; flex-wrap: wrap; }
.cap-tag {
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 8px;
  background: rgba(255,255,255,0.05);
  color: #8b949e;
  border: 1px solid rgba(255,255,255,0.06);
}

.agent-metrics {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  padding: 12px;
  border-radius: 10px;
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.03);
}
.agent-metric-label {
  font-size: 10px;
  color: #8b949e;
  text-transform: uppercase;
  letter-spacing: 0.4px;
  margin-bottom: 3px;
}
.agent-metric-value {
  font-size: 16px;
  font-weight: 700;
}
.agent-metric-value.green { color: #3fb950; }
.agent-metric-value.yellow { color: #d29922; }
.agent-metric-value.red { color: #f85149; }

.sparkline-bar {
  flex: 1;
  min-width: 3px;
  border-radius: 1px 1px 0 0;
  background: rgba(88, 166, 255, 0.3);
}

/* Compare Bar */
.compare-bar {
  background: rgba(22, 27, 40, 0.7);
  border: 1px solid rgba(88, 166, 255, 0.2);
  border-radius: 14px;
  padding: 16px 20px;
  margin-bottom: 20px;
}
.inline-select {
  padding: 6px 10px;
  border-radius: 7px;
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.1);
  color: #e1e4e8;
  font-size: 12px;
  cursor: pointer;
  min-width: 140px;
}
.inline-select:focus {
  outline: none;
  border-color: rgba(88, 166, 255, 0.4);
}
.compare-run-btn {
  padding: 6px 16px;
  border-radius: 7px;
  background: rgba(88, 166, 255, 0.15);
  border: 1px solid rgba(88, 166, 255, 0.3);
  color: #58a6ff;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}
.compare-run-btn:hover:not(:disabled) {
  background: rgba(88, 166, 255, 0.25);
  border-color: rgba(88, 166, 255, 0.5);
}
.compare-run-btn:disabled {
  opacity: 0.4;
  cursor: default;
}
.compare-close-btn {
  background: none;
  border: none;
  color: #8b949e;
  font-size: 18px;
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 4px;
}
.compare-close-btn:hover {
  color: #e1e4e8;
  background: rgba(255,255,255,0.05);
}
.compare-results {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid rgba(255,255,255,0.06);
}
.compare-side-panel {
  padding: 14px;
  border-radius: 10px;
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.04);
}
.compare-agent-name {
  font-size: 14px;
  font-weight: 600;
  color: #e1e4e8;
  margin-bottom: 10px;
}
.compare-metric-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 5px 0;
  font-size: 12px;
  color: #8b949e;
  border-bottom: 1px solid rgba(255,255,255,0.03);
}
.compare-val {
  font-weight: 600;
  color: #e1e4e8;
}
.compare-val.green { color: #3fb950; }
.compare-val.yellow { color: #d29922; }
.compare-val.red { color: #f85149; }

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

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.65);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
}
.modal-container {
  background: #111827;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 18px;
  width: 560px;
  max-width: 95vw;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 24px 80px rgba(0, 0, 0, 0.6);
}
.modal-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 28px 32px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.modal-title { font-size: 20px; margin-bottom: 4px; }
.modal-sub { font-size: 13px; color: #8b949e; margin: 0; }
.modal-close {
  background: none; border: none; color: #8b949e;
  font-size: 24px; cursor: pointer; padding: 4px 8px; border-radius: 6px;
}
.modal-close:hover { color: #e1e4e8; background: rgba(255,255,255,0.06); }
.modal-body {
  padding: 24px 32px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.modal-footer {
  display: flex; align-items: center; gap: 10px;
  padding: 20px 32px; border-top: 1px solid rgba(255, 255, 255, 0.06);
}
.btn-secondary {
  padding: 8px 18px; border-radius: 8px;
  background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.08);
  color: #c9d1d9; font-size: 13px; font-weight: 500; cursor: pointer;
}
.btn-secondary:hover { background: rgba(255,255,255,0.1); }
.btn-primary {
  padding: 8px 22px; border-radius: 8px;
  background: rgba(88, 166, 255, 0.15); border: 1px solid rgba(88, 166, 255, 0.3);
  color: #58a6ff; font-size: 13px; font-weight: 600; cursor: pointer;
}
.btn-primary:hover:not(:disabled) {
  background: rgba(88, 166, 255, 0.25); border-color: rgba(88, 166, 255, 0.5);
}
.btn-primary:disabled { opacity: 0.4; cursor: default; }

/* Form */
.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.form-label {
  font-size: 12px;
  color: #8b949e;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.4px;
}
.required { color: #f85149; }
.form-input {
  padding: 8px 12px;
  border-radius: 8px;
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.08);
  color: #e1e4e8;
  font-size: 13px;
  width: 100%;
  box-sizing: border-box;
}
.form-input:focus {
  outline: none;
  border-color: rgba(88, 166, 255, 0.4);
}
.form-hint {
  font-size: 11px;
  color: #484f58;
  margin: 2px 0 0 0;
}
.kv-row {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 6px;
}
.kv-input {
  flex: 1;
}
.kv-remove {
  background: none;
  border: none;
  color: #f85149;
  font-size: 18px;
  cursor: pointer;
  padding: 0 4px;
  border-radius: 4px;
  flex-shrink: 0;
}
.kv-remove:hover {
  background: rgba(248, 81, 73, 0.1);
}
.kv-add {
  background: none;
  border: 1px dashed rgba(255,255,255,0.1);
  color: #8b949e;
  font-size: 11px;
  padding: 5px 10px;
  border-radius: 6px;
  cursor: pointer;
  margin-top: 2px;
}
.kv-add:hover {
  color: #58a6ff;
  border-color: rgba(88, 166, 255, 0.3);
}
</style>
