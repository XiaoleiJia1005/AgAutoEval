<template>
  <div>
    <div style="margin-bottom: 20px;">
      <router-link :to="`/run/${runId}`" class="link" style="font-size: 13px;">
        &larr; Run {{ runId }}
      </router-link>
    </div>

    <div v-if="loading" class="panel" style="color: #8b949e; text-align: center; padding: 40px;">Loading...</div>
    <div v-else-if="error" class="card" style="color: #f85149;">{{ error }}</div>

    <template v-else>
      <!-- Instance header -->
      <div style="display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 20px; flex-wrap: wrap; gap: 12px;">
        <div>
          <div style="color: #8b949e; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px;">Instance</div>
          <h2 style="margin-bottom: 4px;"><span class="mono">{{ instanceId }}</span></h2>
          <div style="display: flex; gap: 8px; flex-wrap: wrap; align-items: center;">
            <span class="badge badge-gray">{{ info.repo || 'unknown' }}</span>
            <span class="badge" :class="agentBadge(info.agent_type)">{{ info.agent_type }}</span>
          </div>
        </div>
        <div v-if="info.evaluation" style="text-align: right;">
          <div style="color: #8b949e; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px;">Result</div>
          <span class="badge" :class="info.evaluation.resolved ? 'badge-green' : 'badge-red'" style="font-size: 14px; padding: 6px 16px; border-radius: 12px;">
            {{ info.evaluation.resolved ? 'RESOLVED' : 'FAILED' }}
          </span>
        </div>
      </div>

      <!-- Quick stats row -->
      <div class="kpi-grid" style="grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));">
        <div class="kpi-card">
          <div class="kpi-label">Duration</div>
          <div class="kpi-value blue" style="font-size: 20px;">{{ info.evaluation?.duration?.toFixed(1) + 's' || '-' }}</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">F2P Tests</div>
          <div class="kpi-value" :class="info.evaluation?.f2p ? 'green' : 'blue'" style="font-size: 20px;">{{ info.evaluation?.f2p || '-' }}</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">P2P Tests</div>
          <div class="kpi-value blue" style="font-size: 20px;">{{ info.evaluation?.p2p || '-' }}</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Messages</div>
          <div class="kpi-value blue" style="font-size: 20px;">{{ messages.length }}</div>
        </div>
      </div>

      <!-- Problem statement -->
      <div v-if="info.problem_statement" class="panel">
        <h3>Problem Statement</h3>
        <pre class="problem-text">{{ info.problem_statement }}</pre>
      </div>

      <!-- Tabs: Messages | Patch | Logs -->
      <div class="panel" style="padding: 0; overflow: hidden;">
        <div class="tabs">
          <button
            v-for="tab in tabs"
            :key="tab.key"
            :class="['tab', { active: activeTab === tab.key }]"
            @click="activeTab = tab.key"
          >
            <span v-if="tab.key === 'patch' && patchContent" class="tab-dot green"></span>
            <span v-if="tab.key === 'messages' && messages.length" class="tab-dot blue"></span>
            {{ tab.label }}
            <span v-if="tab.key === 'messages' && messages.length" class="tab-count">{{ messages.length }}</span>
            <span v-if="tab.key === 'logs' && logCount" class="tab-count">{{ logCount }}</span>
          </button>
        </div>

        <!-- Messages tab -->
        <div v-if="activeTab === 'messages'" style="padding: 16px 20px;">
          <div v-if="msgLoading" style="color: #8b949e; padding: 20px 0;">Loading messages...</div>
          <div v-else-if="messages.length === 0" style="color: #8b949e; padding: 20px 0;">
            No messages extracted. The agent output may not be in a recognized format.
          </div>
          <MessageList v-else :messages="messages" />
        </div>

        <!-- Patch tab -->
        <div v-if="activeTab === 'patch'" style="padding: 16px 20px;">
          <div v-if="patchContent" style="margin-bottom: 12px; display: flex; gap: 10px; align-items: center;">
            <span class="badge badge-green" v-if="patchStats.additions">+{{ patchStats.additions }}</span>
            <span class="badge badge-red" v-if="patchStats.deletions">-{{ patchStats.deletions }}</span>
            <span class="badge badge-gray">{{ patchStats.files || 0 }} files</span>
          </div>
          <pre class="code-block diff-view" v-if="patchContent" v-html="renderDiff(patchContent)"></pre>
          <div v-else style="color: #8b949e; padding: 20px 0;">No patch available.</div>
        </div>

        <!-- Logs tab -->
        <div v-if="activeTab === 'logs'" style="padding: 16px 20px;">
          <div class="log-files">
            <button
              v-for="(size, name) in info.logs || {}"
              :key="name"
              :class="['log-file-btn', { active: selectedLog === name }]"
              @click="loadLog(name)"
            >
              <span>{{ name }}</span>
              <span class="badge badge-gray">{{ fmtSize(size) }}</span>
            </button>
          </div>
          <div v-if="logLoading" style="color: #8b949e; margin-top: 12px;">Loading...</div>
          <pre class="code-block" v-else-if="logContent">{{ logContent }}</pre>
          <div v-else style="color: #8b949e; margin-top: 12px;">Select a log file to view.</div>
        </div>
      </div>
    </template>
  </div>
</template>

<script>
import { getInstance, getMessages, getRawFile } from '../api.js'
import MessageList from '../components/MessageList.vue'
import { fmtSize, agentBadge } from '../utils.js'

export default {
  name: 'InstanceDetail',
  components: { MessageList },
  props: { runId: String, instanceId: String },
  data() {
    return {
      info: {},
      messages: [],
      patchContent: '',
      loading: true,
      msgLoading: false,
      error: '',
      activeTab: 'messages',
      tabs: [
        { key: 'messages', label: 'Messages' },
        { key: 'patch', label: 'Patch' },
        { key: 'logs', label: 'Raw Logs' },
      ],
      selectedLog: '',
      logContent: '',
      logLoading: false,
    }
  },
  computed: {
    logCount() {
      return Object.keys(this.info.logs || {}).length
    },
    patchStats() {
      if (!this.patchContent) return {}
      const lines = this.patchContent.split('\n')
      let additions = 0, deletions = 0, files = 0
      for (const line of lines) {
        if (line.startsWith('+') && !line.startsWith('+++')) additions++
        else if (line.startsWith('-') && !line.startsWith('---')) deletions++
        else if (line.startsWith('diff --git')) files++
      }
      return { additions, deletions, files }
    },
  },
  async created() {
    try {
      const info = await getInstance(this.runId, this.instanceId)
      this.info = info

      const [msgData, patchText] = await Promise.allSettled([
        getMessages(this.runId, this.instanceId),
        getRawFile(this.runId, this.instanceId, 'patch.diff'),
      ])

      if (msgData.status === 'fulfilled') {
        this.messages = msgData.value.messages || []
      }
      if (patchText.status === 'fulfilled') {
        this.patchContent = patchText.value
      }
    } catch (e) {
      this.error = `Failed to load instance: ${e.message}`
    } finally {
      this.loading = false
    }
  },
  methods: {
    async loadLog(name) {
      this.selectedLog = name
      this.logLoading = true
      try {
        this.logContent = await getRawFile(this.runId, this.instanceId, name)
      } catch (e) {
        this.logContent = `Error loading: ${e.message}`
      } finally {
        this.logLoading = false
      }
    },
    renderDiff(content) {
      const lines = content.split('\n')
      return lines.map(line => {
        let cls = ''
        if (line.startsWith('+') && !line.startsWith('+++')) cls = 'diff-add'
        else if (line.startsWith('-') && !line.startsWith('---')) cls = 'diff-del'
        else if (line.startsWith('@@')) cls = 'diff-hunk'
        else if (line.startsWith('diff ')) cls = 'diff-header'
        else if (line.startsWith('---') || line.startsWith('+++')) cls = 'diff-meta'
        return `<span class="${cls}">${this.escapeHtml(line)}</span>`
      }).join('\n')
    },
    escapeHtml(text) {
      return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    },
    fmtSize,
    agentBadge,
  },
}
</script>

<style scoped>
.problem-text {
  font-size: 13px;
  line-height: 1.65;
  white-space: pre-wrap;
  color: #c9d1d9;
  background: rgba(0, 0, 0, 0.25);
  padding: 18px;
  border-radius: 8px;
  max-height: 220px;
  overflow-y: auto;
  border: 1px solid rgba(255, 255, 255, 0.04);
}
.code-block {
  font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', monospace;
  font-size: 12px;
  line-height: 1.55;
  white-space: pre-wrap;
  color: #c9d1d9;
  background: rgba(0, 0, 0, 0.25);
  padding: 18px;
  border-radius: 8px;
  max-height: 600px;
  overflow-y: auto;
  border: 1px solid rgba(255, 255, 255, 0.04);
}
.diff-view {
  line-height: 1.6;
}
.diff-view :deep(.diff-add) {
  background: rgba(63, 185, 80, 0.12);
  color: #7ee787;
  display: block;
}
.diff-view :deep(.diff-del) {
  background: rgba(248, 81, 73, 0.12);
  color: #ffa198;
  display: block;
}
.diff-view :deep(.diff-hunk) {
  color: #79c0ff;
  display: block;
}
.diff-view :deep(.diff-header) {
  color: #d2a8ff;
  display: block;
  font-weight: 600;
}
.diff-view :deep(.diff-meta) {
  color: #d2a8ff;
  display: block;
  font-weight: 600;
}

/* ── tabs ── */
.tabs {
  display: flex;
  gap: 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  padding: 0 4px;
  background: rgba(0, 0, 0, 0.1);
}
.tab {
  background: none;
  border: none;
  color: #8b949e;
  padding: 12px 20px;
  font-size: 13px;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.15s;
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 500;
}
.tab:hover { color: #e1e4e8; background: rgba(255, 255, 255, 0.02); }
.tab.active {
  color: #e1e4e8;
  border-bottom-color: #58a6ff;
}
.tab-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  display: inline-block;
}
.tab-dot.green { background: #3fb950; }
.tab-dot.blue { background: #58a6ff; }
.tab-count {
  font-size: 10px;
  background: rgba(255, 255, 255, 0.08);
  padding: 1px 6px;
  border-radius: 8px;
  font-weight: 600;
}

/* ── log file buttons ── */
.log-files {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 14px;
}
.log-file-btn {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: #c9d1d9;
  padding: 6px 14px;
  border-radius: 8px;
  font-size: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.15s;
}
.log-file-btn:hover { border-color: rgba(88, 166, 255, 0.3); background: rgba(88, 166, 255, 0.05); }
.log-file-btn.active { border-color: #58a6ff; background: rgba(88, 166, 255, 0.1); }
</style>
