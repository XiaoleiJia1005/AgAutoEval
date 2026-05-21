<template>
  <div>
    <div style="margin-bottom: 20px;">
      <router-link to="/" class="link">&larr; All runs</router-link>
    </div>

    <div v-if="loading" style="color: #8b949e;">Loading...</div>
    <div v-else-if="error" class="card" style="color: #f85149;">{{ error }}</div>

    <template v-else>
      <h2>Run: <span class="mono">{{ runId }}</span></h2>

      <!-- Summary bar -->
      <div class="card" style="display: flex; gap: 32px; flex-wrap: wrap;">
        <div>
          <div style="color: #8b949e; font-size: 12px;">Agent</div>
          <span class="badge" :class="agentBadge(agentType)">{{ agentType }}</span>
        </div>
        <div>
          <div style="color: #8b949e; font-size: 12px;">Instances</div>
          <strong>{{ instances.length }}</strong>
        </div>
        <div v-if="summary.summary">
          <div style="color: #8b949e; font-size: 12px;">Resolved</div>
          <strong>{{ summary.summary.resolved }} / {{ summary.summary.total }}</strong>
        </div>
        <div v-if="summary.summary">
          <div style="color: #8b949e; font-size: 12px;">Accuracy</div>
          <strong>{{ (summary.summary.accuracy * 100).toFixed(1) }}%</strong>
        </div>
        <div v-if="summary.summary">
          <div style="color: #8b949e; font-size: 12px;">Duration</div>
          <strong>{{ formatDuration(summary.summary.total_duration) }}</strong>
        </div>
      </div>

      <!-- Instance table -->
      <h3>Instances</h3>
      <table v-if="instances.length">
        <thead>
          <tr>
            <th>Instance ID</th>
            <th>Repo</th>
            <th>Result</th>
            <th>F2P</th>
            <th>P2P</th>
            <th>Time</th>
            <th>Logs</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="inst in instances" :key="inst.instance_id">
            <td class="mono">{{ inst.instance_id }}</td>
            <td>{{ inst.repo || '-' }}</td>
            <td>
              <span v-if="inst.evaluation" class="badge" :class="inst.evaluation.resolved ? 'badge-green' : 'badge-red'">
                {{ inst.evaluation.resolved ? 'RESOLVED' : 'FAIL' }}
              </span>
              <span v-else class="badge badge-gray">ERROR</span>
            </td>
            <td>
              <span v-if="inst.evaluation && inst.evaluation.f2p">
                {{ inst.evaluation.f2p }}
              </span>
              <span v-else>-</span>
            </td>
            <td>
              <span v-if="inst.evaluation && inst.evaluation.p2p">
                {{ inst.evaluation.p2p }}
              </span>
              <span v-else>-</span>
            </td>
            <td>{{ inst.evaluation ? inst.evaluation.duration.toFixed(1) + 's' : '-' }}</td>
            <td>
              <span v-for="(size, name) in inst.logs" :key="name" class="badge badge-gray" style="margin: 1px;" :title="name + ': ' + size + ' bytes'">
                {{ name.replace('.log', '').replace('agent_', '') }}
              </span>
            </td>
            <td>
              <router-link :to="`/run/${runId}/instance/${inst.instance_id}`" class="link">Messages</router-link>
            </td>
          </tr>
        </tbody>
      </table>
    </template>
  </div>
</template>

<script>
import { getRun } from '../api.js'

export default {
  name: 'RunDetail',
  props: { runId: String },
  data() {
    return { summary: {}, instances: [], agentType: '', loading: true, error: '' }
  },
  async created() {
    try {
      const data = await getRun(this.runId)
      this.summary = data
      this.instances = data.instances || []
      this.agentType = data.agent_type || 'unknown'
    } catch (e) {
      this.error = `Failed to load run: ${e.message}`
    } finally {
      this.loading = false
    }
  },
  methods: {
    formatDuration(s) {
      if (!s || s <= 0) return '-'
      if (s < 60) return `${s.toFixed(0)}s`
      if (s < 3600) return `${Math.floor(s / 60)}m ${Math.floor(s % 60)}s`
      return `${Math.floor(s / 3600)}h ${Math.floor((s % 3600) / 60)}m`
    },
    agentBadge(type) {
      if (type === 'swe_agent') return 'badge-blue'
      if (type === 'claude') return 'badge-green'
      return 'badge-gray'
    },
  },
}
</script>
