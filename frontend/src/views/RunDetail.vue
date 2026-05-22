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
          <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
            <span :class="['status-dot', runStatus.cls]" style="font-size: 12px;">{{ runStatus.label }}</span>
          </div>
          <h2 style="margin-bottom: 4px;"><span class="mono">{{ runId }}</span></h2>
          <div style="display: flex; gap: 8px; flex-wrap: wrap; align-items: center;">
            <span class="badge" :class="agentBadge(agentType)">{{ agentType }}</span>
            <span v-if="meta.provider" class="badge" :class="providerBadge(meta.provider)">{{ meta.provider }}</span>
            <span v-if="meta.model" class="mono" style="font-size: 12px; color: #8b949e;">{{ meta.model }}</span>
            <span class="badge badge-gray" style="font-size: 10px;">SWE-bench Verified</span>
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
      <div class="kpi-grid" style="grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));">
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

      <!-- Split layout: timeline + trace + chart -->
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 24px;">
        <!-- Run Timeline -->
        <div class="panel">
          <h3 style="margin-bottom: 14px;">Run Timeline</h3>
          <div class="timeline">
            <div class="timeline-item done">
              <div class="timeline-dot"></div>
              <div class="timeline-content">
                <div class="timeline-title">Run Started</div>
                <div class="timeline-time">{{ runId.slice(0, 15) }}</div>
              </div>
            </div>
            <div class="timeline-item done">
              <div class="timeline-dot"></div>
              <div class="timeline-content">
                <div class="timeline-title">Environment Setup</div>
                <div class="timeline-time">{{ instances.length }} containers provisioned</div>
              </div>
            </div>
            <div class="timeline-item" :class="sum.accuracy != null ? 'done' : 'active'">
              <div class="timeline-dot"></div>
              <div class="timeline-content">
                <div class="timeline-title">Agent Execution</div>
                <div class="timeline-time">{{ sum.avg_duration != null ? (sum.avg_duration).toFixed(0) + 's avg per task' : 'in progress...' }}</div>
              </div>
            </div>
            <div class="timeline-item" :class="sum.accuracy != null ? 'done' : ''">
              <div class="timeline-dot"></div>
              <div class="timeline-content">
                <div class="timeline-title">Patch Generation</div>
                <div class="timeline-time">{{ sum.resolved != null ? sum.resolved + ' patches applied' : 'pending' }}</div>
              </div>
            </div>
            <div class="timeline-item" :class="sum.accuracy != null ? 'done' : ''">
              <div class="timeline-dot"></div>
              <div class="timeline-content">
                <div class="timeline-title">Test Evaluation</div>
                <div class="timeline-time">{{ sum.f2p != null ? 'F2P: ' + sum.f2p + ', P2P: ' + sum.p2p : 'pending' }}</div>
              </div>
            </div>
            <div class="timeline-item" :class="sum.accuracy != null ? 'done' : ''">
              <div class="timeline-dot"></div>
              <div class="timeline-content">
                <div class="timeline-title">Complete</div>
                <div class="timeline-time">{{ sum.accuracy != null ? (sum.accuracy * 100).toFixed(1) + '% resolved' : 'pending' }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Right side: chart + metadata -->
        <div style="display: flex; flex-direction: column; gap: 16px;">
          <!-- Result Distribution -->
          <div class="panel" style="flex: 1;">
            <h3 style="margin-bottom: 12px;">Result Distribution</h3>
            <div v-if="hasChartData" style="display: flex; align-items: center; gap: 24px; height: calc(100% - 40px);">
              <div style="position: relative; width: 100px; height: 100px;">
                <svg viewBox="0 0 36 36" style="width: 100px; height: 100px; transform: rotate(-90deg);">
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
                    stroke-linecap="round"
                    :style="{ transform: 'rotate(' + (resolvedPct * 3.6) + 'deg)', transformOrigin: 'center' }"
                  />
                </svg>
                <div style="position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;">
                  <div style="text-align: center;">
                    <div style="font-size: 18px; font-weight: 700;" :class="accuracyColor(sum.accuracy)">{{ sum.accuracy != null ? (sum.accuracy * 100).toFixed(0) + '%' : '-' }}</div>
                  </div>
                </div>
              </div>
              <div style="display: flex; flex-direction: column; gap: 8px; font-size: 12px;">
                <div style="display: flex; align-items: center; gap: 8px;">
                  <span style="width: 8px; height: 8px; border-radius: 2px; background: #3fb950;"></span>
                  Resolved: <strong>{{ sum.resolved ?? 0 }}</strong>
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                  <span style="width: 8px; height: 8px; border-radius: 2px; background: #f85149;"></span>
                  Failed: <strong>{{ sum.failed ?? 0 }}</strong>
                </div>
                <div v-if="sum.error_count" style="display: flex; align-items: center; gap: 8px;">
                  <span style="width: 8px; height: 8px; border-radius: 2px; background: #d29922;"></span>
                  Errors: <strong>{{ sum.error_count }}</strong>
                </div>
              </div>
            </div>
            <div v-else style="color: #8b949e; font-size: 13px;">No evaluation results yet.</div>
          </div>

          <!-- Agent Trace placeholder -->
          <div class="panel">
            <h3 style="margin-bottom: 10px;">Agent Trace</h3>
            <div style="color: #8b949e; font-size: 12px; line-height: 1.6;">
              <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                <span style="color: #58a6ff;">&#9679;</span> {{ instances.length }} instances processed
              </div>
              <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                <span style="color: #3fb950;">&#9679;</span> {{ sum.resolved ?? 0 }} patches generated
              </div>
              <div style="display: flex; align-items: center; gap: 8px;">
                <span style="color: #d29922;">&#9679;</span> {{ sum.f2p != null ? sum.f2p : '?' }} fail-to-pass tests
              </div>
            </div>
            <div style="margin-top: 12px; color: #484f58; font-size: 11px;">
              Full trace replay requires agent log recording to be enabled.
            </div>
          </div>
        </div>
      </div>

      <!-- Instances table -->
      <div class="panel" style="padding: 0; overflow: hidden;">
        <div style="padding: 14px 20px; border-bottom: 1px solid rgba(255,255,255,0.05); display: flex; align-items: center; justify-content: space-between;">
          <h3 style="margin-bottom: 0;">Instances</h3>
          <span style="font-size: 11px; color: #8b949e;">{{ instances.length }} total</span>
        </div>
        <table v-if="instances.length">
          <thead>
            <tr>
              <th style="width: 36px;"></th>
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
              <td style="font-size: 12px;">{{ inst.repo || '-' }}</td>
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
              <td style="font-size: 12px;">{{ inst.evaluation?.agent_duration != null ? inst.evaluation.agent_duration.toFixed(1) + 's' : '-' }}</td>
              <td style="font-size: 12px;">{{ inst.evaluation?.duration != null ? inst.evaluation.duration.toFixed(1) + 's' : '-' }}</td>
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
import { formatDuration, agentBadge, providerBadge, accuracyColor, statusInfo } from '../utils.js'

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
    runStatus() {
      return statusInfo({
        accuracy: this.sum.accuracy,
        total: this.sum.total,
        instance_count: this.instances.length,
        error_count: this.sum.error_count,
      })
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

<style scoped>
/* Timeline */
.timeline {
  display: flex;
  flex-direction: column;
  gap: 0;
}
.timeline-item {
  display: flex;
  gap: 14px;
  padding: 10px 0;
  position: relative;
}
.timeline-item:not(:last-child)::after {
  content: '';
  position: absolute;
  left: 6px;
  top: 26px;
  bottom: 0;
  width: 2px;
  background: rgba(255, 255, 255, 0.06);
}
.timeline-item.done:not(:last-child)::after {
  background: rgba(63, 185, 80, 0.3);
}
.timeline-dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.08);
  border: 2px solid rgba(255, 255, 255, 0.1);
  flex-shrink: 0;
  margin-top: 2px;
}
.timeline-item.done .timeline-dot {
  background: rgba(63, 185, 80, 0.2);
  border-color: #3fb950;
}
.timeline-item.active .timeline-dot {
  background: rgba(88, 166, 255, 0.2);
  border-color: #58a6ff;
  animation: pulse 1.8s ease-in-out infinite;
}
@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(88, 166, 255, 0.4); }
  50% { box-shadow: 0 0 0 6px rgba(88, 166, 255, 0); }
}
.timeline-title {
  font-size: 13px;
  color: #8b949e;
  font-weight: 500;
}
.timeline-item.done .timeline-title { color: #e1e4e8; }
.timeline-item.active .timeline-title { color: #58a6ff; }
.timeline-time {
  font-size: 11px;
  color: #484f58;
  margin-top: 2px;
}
.timeline-item.done .timeline-time { color: #8b949e; }
</style>
