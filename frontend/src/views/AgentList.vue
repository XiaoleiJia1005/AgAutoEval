<template>
  <div>
    <!-- Page header -->
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 24px;">
      <div>
        <h2 style="margin-bottom: 4px;">Agents</h2>
        <p style="color: #8b949e; font-size: 13px;">Agent Hub — compare capabilities, performance, and evolution</p>
      </div>
    </div>

    <div v-if="loading" class="panel" style="color: #8b949e; text-align: center; padding: 40px;">Loading agents...</div>
    <div v-else-if="error" class="card" style="color: #f85149;">{{ error }}</div>

    <div v-else-if="agents.length" class="agent-grid">
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

    <div v-else class="panel" style="color: #8b949e; text-align: center; padding: 48px 24px;">
      <p style="font-size: 15px; margin-bottom: 8px;">No agents found.</p>
      <p style="font-size: 13px;">Run an evaluation to populate agent data.</p>
    </div>
  </div>
</template>

<script>
import { getRuns } from '../api.js'
import { agentBadge, accuracyColor, agentLabel } from '../utils.js'
import { AGENT_TYPES } from '../utils.js'

export default {
  name: 'AgentList',
  data() {
    return { agents: [], loading: true, error: '' }
  },
  async created() {
    try {
      const data = await getRuns()
      const runs = data.runs || []
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
    agentBadgeClass(type) {
      return agentBadge(type).replace('badge-', '')
    },
    buildAgents(runs) {
      // Group runs by agent_type
      const groups = {}
      for (const r of runs) {
        const type = r.agent_type || 'unknown'
        if (!groups[type]) {
          groups[type] = []
        }
        groups[type].push(r)
      }

      // Static agent definitions for capabilities/descriptions
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
          latestAccuracy: accuracies.length ? (Math.max(...accuracies) * 100) : null, // we'll refine this
          bestAccuracy: accuracies.length ? (Math.max(...accuracies) * 100) : null,
          latestVersion,
          benchmarkCount: 1, // currently just SWE-bench
          runCount: agentRuns.length,
          lastActive: this.timeAgo(agentRuns[0]?.run_id),
          lastActiveStatus: withAcc.length > 0 ? 'status-done' : 'status-queued',
          accuracyHistory: accuracies.slice(0, 10).reverse(),
        }
      }).sort((a, b) => (b.bestAccuracy || 0) - (a.bestAccuracy || 0))
    },
    timeAgo(runId) {
      if (!runId) return 'unknown'
      // Extract timestamp from run_id format: YYYYmmdd_HHMMSS
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
</style>
