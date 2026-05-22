<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-container">
      <div class="modal-header">
        <div>
          <h2 class="modal-title">Compare Traces</h2>
          <p class="modal-sub">Select two runs to compare execution traces</p>
        </div>
        <button class="modal-close" @click="$emit('close')">&times;</button>
      </div>

      <div class="compare-body">
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px;">
          <!-- Baseline -->
          <div>
            <div class="compare-section-label">Baseline</div>
            <select v-model="baseline" class="compare-select">
              <option value="">Select baseline run...</option>
              <option v-for="r in runsWithData" :key="r.run_id" :value="r.run_id">{{ r.run_id }}</option>
            </select>
            <div v-if="baselineInfo" class="compare-run-info">
              <span class="badge" :class="agentBadgeClass(baselineInfo.agent_type)">{{ baselineInfo.agent_type }}</span>
              <span class="mono" style="font-size: 11px;">{{ baselineInfo.model || '-' }}</span>
              <span v-if="baselineInfo.accuracy != null" style="font-size: 12px; color: #3fb950;">{{ (baselineInfo.accuracy * 100).toFixed(1) }}%</span>
            </div>
          </div>
          <!-- Comparison -->
          <div>
            <div class="compare-section-label">Comparison</div>
            <select v-model="comparison" class="compare-select">
              <option value="">Select comparison run...</option>
              <option v-for="r in runsWithData" :key="r.run_id" :value="r.run_id">{{ r.run_id }}</option>
            </select>
            <div v-if="comparisonInfo" class="compare-run-info">
              <span class="badge" :class="agentBadgeClass(comparisonInfo.agent_type)">{{ comparisonInfo.agent_type }}</span>
              <span class="mono" style="font-size: 11px;">{{ comparisonInfo.model || '-' }}</span>
              <span v-if="comparisonInfo.accuracy != null" style="font-size: 12px; color: #3fb950;">{{ (comparisonInfo.accuracy * 100).toFixed(1) }}%</span>
            </div>
          </div>
        </div>

        <!-- Quick compare insight -->
        <div v-if="baselineInfo && comparisonInfo" class="compare-preview">
          <h4 style="color: #8b949e; font-size: 12px; margin-bottom: 12px;">Comparison Preview</h4>
          <div style="display: grid; grid-template-columns: 1fr auto 1fr; gap: 16px; align-items: center;">
            <div class="compare-side">
              <div class="compare-metric-label">Accuracy</div>
              <div class="compare-metric-value">{{ baselineInfo.accuracy != null ? (baselineInfo.accuracy * 100).toFixed(1) + '%' : '-' }}</div>
              <div class="compare-metric-label">Instances</div>
              <div class="compare-metric-value">{{ baselineInfo.instance_count }}</div>
              <div class="compare-metric-label">Duration</div>
              <div class="compare-metric-value">{{ formatDuration(baselineInfo.total_duration) }}</div>
            </div>
            <div style="text-align: center; color: #484f58; font-size: 24px;">vs</div>
            <div class="compare-side">
              <div class="compare-metric-label">Accuracy</div>
              <div class="compare-metric-value">
                {{ comparisonInfo.accuracy != null ? (comparisonInfo.accuracy * 100).toFixed(1) + '%' : '-' }}
                <span v-if="delta !== null" :class="delta >= 0 ? 'delta-up' : 'delta-down'">{{ delta >= 0 ? '+' : '' }}{{ delta.toFixed(1) }}pp</span>
              </div>
              <div class="compare-metric-label">Instances</div>
              <div class="compare-metric-value">{{ comparisonInfo.instance_count }}</div>
              <div class="compare-metric-label">Duration</div>
              <div class="compare-metric-value">{{ formatDuration(comparisonInfo.total_duration) }}</div>
            </div>
          </div>
        </div>
      </div>

      <div class="modal-footer">
        <div style="flex: 1;"></div>
        <button class="btn-secondary" @click="$emit('close')">Cancel</button>
        <button class="btn-primary" :disabled="!canCompare" @click="compare">
          <span v-html="dimIcon('compare')" style="display: flex; align-items: center;"></span>
          Compare
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { getRuns } from '../api.js'
import { formatDuration, agentBadge, dimIcon } from '../utils.js'

export default {
  name: 'CompareModal',
  emits: ['close'],
  props: {
    initialRunId: { type: String, default: '' },
  },
  data() {
    return {
      runs: [],
      baseline: this.initialRunId,
      comparison: '',
    }
  },
  computed: {
    runsWithData() {
      return this.runs.filter(r => r.accuracy != null)
    },
    baselineInfo() {
      return this.runs.find(r => r.run_id === this.baseline)
    },
    comparisonInfo() {
      return this.runs.find(r => r.run_id === this.comparison)
    },
    canCompare() {
      return this.baseline && this.comparison && this.baseline !== this.comparison
    },
    delta() {
      if (!this.baselineInfo || !this.comparisonInfo) return null
      if (this.baselineInfo.accuracy == null || this.comparisonInfo.accuracy == null) return null
      return (this.comparisonInfo.accuracy - this.baselineInfo.accuracy) * 100
    },
  },
  async created() {
    try {
      const data = await getRuns()
      this.runs = data.runs || []
    } catch (_) {
      this.runs = []
    }
  },
  methods: {
    agentBadgeClass(type) {
      return agentBadge(type)
    },
    formatDuration,
    dimIcon,
    compare() {
      if (!this.canCompare) return
      alert('Compare ' + this.baseline + ' vs ' + this.comparison + '\n\nFull trace comparison requires backend trace data support.')
      this.$emit('close')
    },
  },
}
</script>

<style scoped>
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
  width: 600px;
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

.compare-body { padding: 24px 32px; }
.compare-section-label {
  font-size: 10px; color: #8b949e; text-transform: uppercase;
  letter-spacing: 0.6px; margin-bottom: 8px; font-weight: 600;
}
.compare-select {
  width: 100%; padding: 8px 12px; border-radius: 8px;
  background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.08);
  color: #e1e4e8; font-size: 13px; cursor: pointer;
}
.compare-select:focus { outline: none; border-color: rgba(88, 166, 255, 0.4); }
.compare-run-info {
  display: flex; align-items: center; gap: 8px; margin-top: 8px;
}

.compare-preview {
  padding: 16px; border-radius: 10px;
  background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.04);
}
.compare-side { display: flex; flex-direction: column; gap: 4px; }
.compare-metric-label { font-size: 10px; color: #8b949e; text-transform: uppercase; letter-spacing: 0.4px; }
.compare-metric-value { font-size: 14px; font-weight: 600; }
.delta-up { color: #3fb950; font-size: 11px; margin-left: 4px; }
.delta-down { color: #f85149; font-size: 11px; margin-left: 4px; }

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
  display: flex; align-items: center; gap: 6px;
}
.btn-primary:hover:not(:disabled) {
  background: rgba(88, 166, 255, 0.25); border-color: rgba(88, 166, 255, 0.5);
}
.btn-primary:disabled {
  opacity: 0.4; cursor: default;
}
.btn-primary :deep(svg) { stroke: currentColor; }
</style>
