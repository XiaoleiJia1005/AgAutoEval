<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-container">
      <!-- Header -->
      <div class="modal-header">
        <div>
          <h2 class="modal-title">Launch Evaluation</h2>
          <p class="modal-sub">Configure and start a new agent evaluation run</p>
        </div>
        <button class="modal-close" @click="$emit('close')">&times;</button>
      </div>

      <!-- Step indicator -->
      <div class="steps">
        <div
          v-for="(s, i) in steps"
          :key="i"
          :class="['step', { active: step === i, done: step > i }]"
          @click="step = i"
        >
          <span class="step-num">{{ step > i ? '&#10003;' : i + 1 }}</span>
          <span class="step-label">{{ s }}</span>
        </div>
      </div>

      <!-- Step content -->
      <div class="step-body">
        <!-- Step 0: Benchmark -->
        <div v-if="step === 0">
          <h3>Select Benchmark</h3>
          <div class="option-grid">
            <div
              v-for="b in benchmarks"
              :key="b.id"
              :class="['option-card', { selected: form.benchmark === b.id }]"
              @click="form.benchmark = b.id"
            >
              <div class="option-radio"><span v-if="form.benchmark === b.id"></span></div>
              <div>
                <div class="option-title">{{ b.label }}</div>
                <div class="option-desc">{{ b.tasks }} tasks · {{ b.lang }} · {{ b.difficulty }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Step 1: Agent -->
        <div v-if="step === 1">
          <h3>Select Agent</h3>
          <div class="option-grid">
            <div
              v-for="a in agentTypes"
              :key="a.id"
              :class="['option-card', { selected: form.agent === a.id }]"
              @click="form.agent = a.id"
            >
              <div class="option-radio"><span v-if="form.agent === a.id"></span></div>
              <div>
                <div class="option-title">{{ a.label }}</div>
                <div class="option-desc">{{ a.desc }}</div>
                <div class="capability-tags">
                  <span v-for="c in a.capabilities" :key="c" class="cap-tag">{{ c }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Step 2: Model -->
        <div v-if="step === 2">
          <h3>Select Model</h3>
          <div style="display: flex; flex-direction: column; gap: 16px;">
            <div v-for="p in providers" :key="p.id" style="margin-bottom: 8px;">
              <div style="font-size: 13px; font-weight: 600; color: #8b949e; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.5px; display: flex; align-items: center; gap: 8px;">
                <span class="provider-icon-svg" v-html="providerSvg(p.id)"></span>
                {{ p.label }}
              </div>
              <div class="option-grid" style="grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));">
                <div
                  v-for="m in p.models"
                  :key="m"
                  :class="['option-card', { selected: form.provider === p.id && form.model === m }]"
                  @click="form.provider = p.id; form.model = m"
                >
                  <div class="option-radio"><span v-if="form.provider === p.id && form.model === m"></span></div>
                  <div class="option-title" style="font-size: 13px;">{{ m }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Step 3: Runtime Config -->
        <div v-if="step === 3">
          <h3>Runtime Configuration</h3>
          <div class="config-grid">
            <div class="config-field">
              <label>Timeout (minutes)</label>
              <input v-model.number="form.timeout" type="number" min="1" max="360" class="config-input" />
            </div>
            <div class="config-field">
              <label>Parallel Workers</label>
              <input v-model.number="form.parallelism" type="number" min="1" max="64" class="config-input" />
            </div>
            <div class="config-field">
              <label>Sandbox Mode</label>
              <select v-model="form.sandboxMode" class="config-input">
                <option value="auto">Auto (clone + install)</option>
                <option value="prebuilt">Prebuilt image</option>
              </select>
            </div>
            <div class="config-field">
              <label>Retry Strategy</label>
              <select v-model="form.retryStrategy" class="config-input">
                <option value="none">None</option>
                <option value="once">Retry once</option>
                <option value="adaptive">Adaptive</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Step 4: Eval Config -->
        <div v-if="step === 4">
          <h3>Evaluation Options</h3>
          <div class="config-grid">
            <div class="config-field">
              <label>Limit Instances</label>
              <input v-model.number="form.limitInstances" type="number" min="0" placeholder="0 = all" class="config-input" />
            </div>
            <div class="config-field">
              <label>Random Seed</label>
              <input v-model.number="form.seed" type="number" min="0" class="config-input" />
            </div>
          </div>
          <div style="display: flex; flex-direction: column; gap: 10px; margin-top: 12px;">
            <label class="toggle-row">
              <input type="checkbox" v-model="form.enableReplay" />
              <span>Enable agent trace recording</span>
            </label>
            <label class="toggle-row">
              <input type="checkbox" v-model="form.enablePatchGrading" />
              <span>Enable patch grading</span>
            </label>
          </div>
        </div>

        <!-- Step 5: Review -->
        <div v-if="step === 5">
          <h3>Review &amp; Launch</h3>
          <div class="review-grid">
            <div class="review-item">
              <span class="review-label">Benchmark</span>
              <span>{{ selectedBenchmark?.label || '-' }}</span>
            </div>
            <div class="review-item">
              <span class="review-label">Agent</span>
              <span>{{ selectedAgent?.label || form.agent || '-' }}</span>
            </div>
            <div class="review-item">
              <span class="review-label">Model</span>
              <span>{{ form.model || '-' }} <span style="color: #8b949e;">({{ form.provider }})</span></span>
            </div>
            <div class="review-item">
              <span class="review-label">Instances</span>
              <span>{{ form.limitInstances > 0 ? form.limitInstances : 'All (' + (selectedBenchmark?.tasks || '?') + ')' }}</span>
            </div>
            <div class="review-item">
              <span class="review-label">Max Runtime</span>
              <span>{{ form.timeout }} min · {{ form.parallelism }} workers</span>
            </div>
            <div class="review-item">
              <span class="review-label">Estimated Cost</span>
              <span class="mono" style="color: #3fb950; font-weight: 600;">${{ estimatedCost }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="modal-footer">
        <button v-if="step > 0" class="btn-secondary" @click="step--">Back</button>
        <div style="flex: 1;"></div>
        <button class="btn-secondary" @click="$emit('close')">Cancel</button>
        <button v-if="step < 5" class="btn-primary" @click="step++">Continue</button>
        <button v-else class="btn-primary launch-submit" @click="launch">
          <span>&#9889;</span> Launch Evaluation
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { BENCHMARKS, AGENT_TYPES, PROVIDERS, providerSvg } from '../utils.js'

export default {
  name: 'LaunchRunModal',
  emits: ['close'],
  data() {
    return {
      step: 0,
      steps: ['Benchmark', 'Agent', 'Model', 'Runtime', 'Options', 'Review'],
      benchmarks: BENCHMARKS,
      agentTypes: AGENT_TYPES,
      providers: PROVIDERS,
      form: {
        benchmark: BENCHMARKS[0].id,
        agent: AGENT_TYPES[0].id,
        provider: 'anthropic',
        model: 'Claude Sonnet 4.6',
        maxIterations: 100,
        timeout: 90,
        parallelism: 8,
        temperature: 0.0,
        sandboxMode: 'auto',
        retryStrategy: 'none',
        limitInstances: 0,
        seed: 42,
        enableReplay: true,
        enablePatchGrading: true,
      },
    }
  },
  computed: {
    selectedBenchmark() {
      return this.benchmarks.find(b => b.id === this.form.benchmark)
    },
    selectedAgent() {
      return this.agentTypes.find(a => a.id === this.form.agent)
    },
    estimatedCost() {
      const tasks = this.form.limitInstances > 0 ? this.form.limitInstances : (this.selectedBenchmark?.tasks || 50)
      const costPerTask = (this.form.provider === 'anthropic' || this.form.provider === 'openai') ? 0.28 : 0.08
      return (tasks * costPerTask).toFixed(2)
    },
  },
  methods: {
    providerSvg,
    launch() {
      alert('Launch triggered!\n\n' + JSON.stringify(this.form, null, 2))
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
  width: 680px;
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
.modal-title {
  font-size: 20px;
  margin-bottom: 4px;
}
.modal-sub {
  font-size: 13px;
  color: #8b949e;
  margin: 0;
}
.modal-close {
  background: none;
  border: none;
  color: #8b949e;
  font-size: 24px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
}
.modal-close:hover { color: #e1e4e8; background: rgba(255,255,255,0.06); }

/* Steps */
.steps {
  display: flex;
  gap: 2px;
  padding: 20px 32px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}
.step {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #484f58;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: color 0.15s;
  white-space: nowrap;
}
.step:hover { color: #8b949e; }
.step.active { color: #58a6ff; }
.step.done { color: #3fb950; }
.step-num {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: rgba(255,255,255,0.06);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 600;
}
.step.active .step-num { background: rgba(88, 166, 255, 0.15); }
.step.done .step-num { background: rgba(63, 185, 80, 0.15); font-size: 10px; }

/* Step body */
.step-body {
  padding: 24px 32px;
  min-height: 280px;
}

/* Option cards */
.option-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 8px;
}
.option-card {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 14px 16px;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  cursor: pointer;
  transition: all 0.15s;
}
.option-card:hover { border-color: rgba(88, 166, 255, 0.2); background: rgba(88, 166, 255, 0.04); }
.option-card.selected { border-color: rgba(88, 166, 255, 0.4); background: rgba(88, 166, 255, 0.08); }
.option-radio {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 2px solid rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 1px;
}
.option-card.selected .option-radio { border-color: #58a6ff; }
.option-card.selected .option-radio span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #58a6ff;
  display: block;
}
.option-title { font-size: 14px; font-weight: 600; color: #e1e4e8; }
.option-desc { font-size: 12px; color: #8b949e; margin-top: 2px; }
.capability-tags { display: flex; gap: 4px; margin-top: 6px; flex-wrap: wrap; }
.cap-tag {
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 8px;
  background: rgba(255,255,255,0.05);
  color: #8b949e;
}

/* Config fields */
.config-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}
.config-field label {
  display: block;
  font-size: 12px;
  color: #8b949e;
  margin-bottom: 6px;
  font-weight: 500;
}
.config-input {
  width: 100%;
  padding: 8px 12px;
  border-radius: 8px;
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.08);
  color: #e1e4e8;
  font-size: 13px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}
.config-input:focus { outline: none; border-color: rgba(88, 166, 255, 0.4); }
select.config-input { cursor: pointer; }

.toggle-row {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  color: #c9d1d9;
  cursor: pointer;
}
.toggle-row input[type="checkbox"] { accent-color: #58a6ff; width: 16px; height: 16px; }

/* Review */
.review-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.review-item {
  padding: 12px 16px;
  border-radius: 8px;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.04);
  font-size: 13px;
}
.review-label {
  display: block;
  font-size: 10px;
  color: #8b949e;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 4px;
  font-weight: 600;
}

/* Footer */
.modal-footer {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 20px 32px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}
.btn-secondary {
  padding: 8px 18px;
  border-radius: 8px;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.08);
  color: #c9d1d9;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}
.btn-secondary:hover { background: rgba(255,255,255,0.1); }
.btn-primary {
  padding: 8px 22px;
  border-radius: 8px;
  background: rgba(88, 166, 255, 0.15);
  border: 1px solid rgba(88, 166, 255, 0.3);
  color: #58a6ff;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
}
.btn-primary:hover {
  background: rgba(88, 166, 255, 0.25);
  border-color: rgba(88, 166, 255, 0.5);
}
.provider-icon-svg {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.launch-submit {
  background: rgba(63, 185, 80, 0.15);
  border-color: rgba(63, 185, 80, 0.3);
  color: #3fb950;
}
.launch-submit:hover {
  background: rgba(63, 185, 80, 0.25);
  border-color: rgba(63, 185, 80, 0.5);
  box-shadow: 0 0 20px rgba(63, 185, 80, 0.2);
}
</style>
