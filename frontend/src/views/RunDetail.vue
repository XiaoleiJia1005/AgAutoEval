<template>
  <div>
    <div style="margin-bottom: 20px;">
      <router-link to="/" class="link" style="font-size: 13px;">&larr; All runs</router-link>
    </div>

    <div v-if="loading" class="panel" style="color: #8b949e; text-align: center; padding: 40px;">Loading...</div>
    <div v-else-if="error" class="card" style="color: #f85149;">{{ error }}</div>

    <template v-else>
      <!-- Run header -->
      <div style="display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 20px; flex-wrap: wrap; gap: 16px;">
        <div>
          <div style="color: #8b949e; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px;">Run</div>
          <h2 style="margin-bottom: 4px;"><span class="mono">{{ runId }}</span></h2>
          <div style="display: flex; gap: 8px; flex-wrap: wrap; align-items: center;">
            <span class="badge" :class="agentBadge(agentType)">{{ agentType }}</span>
            <span v-if="meta.provider" class="badge" :class="providerBadge(meta.provider)">{{ meta.provider }}</span>
            <span v-if="meta.model" class="mono" style="font-size: 12px; color: #8b949e;">{{ meta.model }}</span>
          </div>
        </div>
        <div v-if="sum.accuracy != null" style="text-align: right;">
          <div style="color: #8b949e; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">Accuracy</div>
          <div :class="['kpi-value', accuracyColor(sum.accuracy)]" style="font-size: 36px;">
            {{ (sum.accuracy * 100).toFixed(1) }}%
          </div>
        </div>
      </div>

      <!-- Summary stats -->
      <div class="kpi-grid" style="grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));">
        <div class="kpi-card">
          <div class="kpi-label">Instances</div>
          <div class="kpi-value blue" style="font-size: 24px;">{{ instances.length }}</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Resolved</div>
          <div class="kpi-value green" style="font-size: 24px;">{{ sum.resolved ?? '-' }}</div>
          <div class="kpi-sub">of {{ sum.total ?? '-' }} total</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Failed</div>
          <div class="kpi-value red" style="font-size: 24px;">{{ sum.failed ?? '-' }}</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Avg Agent Time</div>
          <div class="kpi-value blue" style="font-size: 24px;">{{ sum.avg_duration != null ? sum.avg_duration.toFixed(1) + 's' : '-' }}</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Total Duration</div>
          <div class="kpi-value blue" style="font-size: 24px;">{{ formatDuration(sum.total_duration) }}</div>
        </div>
      </div>

      <!-- Pass/fail chart + metadata -->
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 24px;">
        <div class="panel">
          <h3 style="margin-bottom: 12px;">Result Distribution</h3>
          <div v-if="hasChartData" style="display: flex; align-items: center; gap: 24px;">
            <div style="position: relative; width: 120px; height: 120px;">
              <svg viewBox="0 0 36 36" style="width: 120px; height: 120px; transform: rotate(-90deg);">
                <circle cx="18" cy="18" r="15" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="3.5" />
                <circle
                  v-if="resolvedPct > 0"
                  cx="18" cy="18" r="15" fill="none"
                  stroke="#3fb950" stroke-width="3.5"
                  :stroke-dasharray="resolvedPct + ' ' + (100 - resolvedPct)"
                  stroke-linecap="round"
                />
                <circle
                  v-if="failedPct > 0"
                  cx="18" cy="18" r="15" fill="none"
                  stroke="#f85149" stroke-width="3.5"
                  :stroke-dasharray="failedPct + ' ' + (100 - failedPct)"
                  :stroke-dashoffset="-1"
                  stroke-linecap="round"
                  :style="{ transform: 'rotate(' + (resolvedPct * 3.6) + 'deg)', transformOrigin: 'center' }"
                />
              </svg>
              <div style="position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;">
                <div style="text-align: center;">
                  <div style="font-size: 20px; font-weight: 700;" :class="accuracyColor(sum.accuracy)">{{ sum.accuracy != null ? (sum.accuracy * 100).toFixed(0) + '%' : '-' }}</div>
                  <div style="font-size: 10px; color: #8b949e;">pass rate</div>
                </div>
              </div>
            </div>
            <div style="display: flex; flex-direction: column; gap: 10px; font-size: 13px;">
              <div style="display: flex; align-items: center; gap: 8px;">
                <span style="width: 10px; height: 10px; border-radius: 3px; background: #3fb950; display: inline-block;"></span>
                Resolved: <strong>{{ sum.resolved ?? 0 }}</strong>
              </div>
              <div style="display: flex; align-items: center; gap: 8px;">
                <span style="width: 10px; height: 10px; border-radius: 3px; background: #f85149; display: inline-block;"></span>
                Failed: <strong>{{ sum.failed ?? 0 }}</strong>
              </div>
              <div v-if="sum.error_count" style="display: flex; align-items: center; gap: 8px;">
                <span style="width: 10px; height: 10px; border-radius: 3px; background: #d29922; display: inline-block;"></span>
                Errors: <strong>{{ sum.error_count }}</strong>
              </div>
            </div>
          </div>
          <div v-else style="color: #8b949e; font-size: 13px;">No evaluation results yet.</div>
        </div>

        <div class="panel">
          <h3 style="margin-bottom: 12px;">Run Metadata</h3>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 13px;">
            <div>
              <div style="color: #8b949e; font-size: 11px; margin-bottom: 2px;">Dataset</div>
              <span>{{ meta.dataset_path || '-' }}</span>
            </div>
            <div>
              <div style="color: #8b949e; font-size: 11px; margin-bottom: 2px;">Format</div>
              <span>{{ meta.dataset_provider || '-' }}</span>
            </div>
            <div v-if="sum.f2p != null">
              <div style="color: #8b949e; font-size: 11px; margin-bottom: 2px;">F2P Tests</div>
              <span class="mono">{{ sum.f2p }}</span>
            </div>
            <div v-if="sum.p2p != null">
              <div style="color: #8b949e; font-size: 11px; margin-bottom: 2px;">P2P Tests</div>
              <span class="mono">{{ sum.p2p }}</span>
            </div>
            <div>
              <div style="color: #8b949e; font-size: 11px; margin-bottom: 2px;">Agent Type</div>
              <span>{{ agentType }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Instances table -->
      <div class="panel" style="padding: 0; overflow: hidden;">
        <div style="padding: 16px 20px; border-bottom: 1px solid rgba(255,255,255,0.05);">
          <h3 style="margin-bottom: 0;">Instances</h3>
        </div>
        <table v-if="instances.length">
          <thead>
            <tr>
              <th style="width: 40px;"></th>
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
              <td style="padding-right: 0;">
                <span v-if="inst.evaluation" :class="['status-dot', inst.evaluation.resolved ? 'status-done' : 'status-failed']"></span>
                <span v-else class="status-dot status-failed"></span>
              </td>
              <td class="mono">{{ inst.instance_id }}</td>
              <td>{{ inst.repo || '-' }}</td>
              <td>
                <span v-if="inst.evaluation" class="badge" :class="inst.evaluation.resolved ? 'badge-green' : 'badge-red'">
                  {{ inst.evaluation.resolved ? 'RESOLVED' : 'FAIL' }}
                </span>
                <span v-else class="badge badge-yellow">ERROR</span>
              </td>
              <td>
                <span v-if="inst.evaluation && inst.evaluation.f2p" class="mono" style="font-size: 11px;">
                  {{ inst.evaluation.f2p }}
                </span>
                <span v-else style="color: #484f58;">-</span>
              </td>
              <td>
                <span v-if="inst.evaluation && inst.evaluation.p2p" class="mono" style="font-size: 11px;">
                  {{ inst.evaluation.p2p }}
                </span>
                <span v-else style="color: #484f58;">-</span>
              </td>
              <td>{{ inst.evaluation?.agent_duration != null ? inst.evaluation.agent_duration.toFixed(1) + 's' : '-' }}</td>
              <td>{{ inst.evaluation?.duration != null ? inst.evaluation.duration.toFixed(1) + 's' : '-' }}</td>
              <td>
                <span v-for="(size, name) in inst.logs" :key="name" class="badge badge-gray" style="margin: 1px;" :title="name + ': ' + size + ' bytes'">
                  {{ name.replace('.log', '').replace('agent_', '') }}
                </span>
              </td>
              <td>
                <router-link :to="`/run/${runId}/instance/${inst.instance_id}`" class="link" style="font-size: 12px;">Messages &rarr;</router-link>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
  </div>
</template>

<script>
import { getRun } from '../api.js'
import { formatDuration, agentBadge, providerBadge, accuracyColor } from '../utils.js'

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
    hasChartData() {
      return (this.sum.resolved > 0 || this.sum.failed > 0)
    },
    totalForChart() {
      return (this.sum.resolved ?? 0) + (this.sum.failed ?? 0) + (this.sum.error_count ?? 0)
    },
    resolvedPct() {
      if (!this.totalForChart) return 0
      return ((this.sum.resolved ?? 0) / this.totalForChart) * 100
    },
    failedPct() {
      if (!this.totalForChart) return 0
      return ((this.sum.failed ?? 0) / this.totalForChart) * 100
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
  methods: { formatDuration, agentBadge, providerBadge, accuracyColor },
}
</script>
