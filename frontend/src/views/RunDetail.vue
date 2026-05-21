<template>
  <div>
    <div style="margin-bottom: 20px;">
      <router-link to="/" class="link">&larr; All runs</router-link>
    </div>

    <div v-if="loading" style="color: #8b949e;">Loading...</div>
    <div v-else-if="error" class="card" style="color: #f85149;">{{ error }}</div>

    <template v-else>
      <h2>Run: <span class="mono">{{ runId }}</span></h2>

      <div class="card">
        <h3>Overview</h3>
        <div class="summary-grid">
          <div>
            <div class="sum-label">Agent</div>
            <span class="badge" :class="agentBadge(agentType)">{{ agentType }}</span>
          </div>
          <div v-if="meta.provider">
            <div class="sum-label">Provider</div>
            <span class="badge" :class="providerBadge(meta.provider)">{{ meta.provider }}</span>
          </div>
          <div v-if="meta.model">
            <div class="sum-label">Model</div>
            <span class="mono" style="font-size: 13px;">{{ meta.model }}</span>
          </div>
          <div v-if="meta.dataset_path">
            <div class="sum-label">Dataset</div>
            <span style="font-size: 13px;">{{ meta.dataset_path }}</span>
          </div>
          <div v-if="meta.dataset_provider">
            <div class="sum-label">Dataset Format</div>
            <span class="badge badge-gray">{{ meta.dataset_provider }}</span>
          </div>
        </div>

        <div class="summary-grid" style="margin-top: 16px; padding-top: 16px; border-top: 1px solid #30363d;">
          <div>
            <div class="sum-label">Instances</div>
            <strong>{{ instances.length }}</strong>
          </div>
          <div>
            <div class="sum-label">Resolved</div>
            <strong>
              <span class="badge badge-green">{{ sum.resolved ?? '-' }}</span>
              /
              <span>{{ sum.total ?? '-' }}</span>
            </strong>
          </div>
          <div>
            <div class="sum-label">Failed</div>
            <strong>
              <span class="badge badge-red">{{ sum.failed ?? '-' }}</span>
            </strong>
          </div>
          <div>
            <div class="sum-label">Accuracy</div>
            <strong>{{ sum.accuracy != null ? (sum.accuracy * 100).toFixed(1) + '%' : '-' }}</strong>
          </div>
          <div v-if="sum.f2p">
            <div class="sum-label">F2P</div>
            <strong class="mono">{{ sum.f2p }}</strong>
          </div>
          <div v-if="sum.p2p">
            <div class="sum-label">P2P</div>
            <strong class="mono">{{ sum.p2p }}</strong>
          </div>
          <div>
            <div class="sum-label">Total Duration</div>
            <strong>{{ formatDuration(sum.total_duration) }}</strong>
          </div>
          <div>
            <div class="sum-label">avg agent time</div>
            <strong>{{ sum.avg_duration != null ? sum.avg_duration.toFixed(1) + 's' : '-' }}</strong>
          </div>
        </div>
      </div>

      <h3>Instances</h3>
      <table v-if="instances.length">
        <thead>
          <tr>
            <th>Instance ID</th>
            <th>Repo</th>
            <th>Result</th>
            <th>F2P</th>
            <th>P2P</th>
            <th>Agent Time</th>
            <th>Total Time</th>
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
              <span v-if="inst.evaluation && inst.evaluation.f2p" class="mono" style="font-size: 11px;">
                {{ inst.evaluation.f2p }}
              </span>
              <span v-else>-</span>
            </td>
            <td>
              <span v-if="inst.evaluation && inst.evaluation.p2p" class="mono" style="font-size: 11px;">
                {{ inst.evaluation.p2p }}
              </span>
              <span v-else>-</span>
            </td>
            <td>{{ inst.evaluation?.agent_duration != null ? inst.evaluation.agent_duration.toFixed(1) + 's' : '-' }}</td>
            <td>{{ inst.evaluation?.duration != null ? inst.evaluation.duration.toFixed(1) + 's' : '-' }}</td>
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
import { formatDuration, agentBadge, providerBadge } from '../utils.js'

export default {
  name: 'RunDetail',
  props: { runId: String },
  data() {
    return { summary: {}, instances: [], agentType: '', loading: true, error: '' }
  },
  computed: {
    sum() {
      return this.summary.summary || {}
    },
    meta() {
      return this.summary.summary?.metadata || {}
    },
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
  methods: { formatDuration, agentBadge, providerBadge },
}
</script>

<style scoped>
.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 16px;
}
.sum-label {
  color: #8b949e;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 4px;
}
</style>
