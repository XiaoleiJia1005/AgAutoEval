<template>
  <div>
    <div style="margin-bottom: 20px;">
      <router-link :to="`/run/${runId}`" class="link">
        &larr; Run {{ runId }}
      </router-link>
    </div>

    <div v-if="loading" style="color: #8b949e;">Loading...</div>
    <div v-else-if="error" class="card" style="color: #f85149;">{{ error }}</div>

    <template v-else>
      <h2>Instance: <span class="mono">{{ instanceId }}</span></h2>

      <!-- Instance info bar -->
      <div class="card" style="display: flex; gap: 32px; flex-wrap: wrap;">
        <div>
          <div style="color: #8b949e; font-size: 12px;">Repo</div>
          <strong>{{ info.repo || '-' }}</strong>
        </div>
        <div>
          <div style="color: #8b949e; font-size: 12px;">Agent</div>
          <span class="badge" :class="agentBadge(info.agent_type)">{{ info.agent_type }}</span>
        </div>
        <div v-if="info.evaluation">
          <div style="color: #8b949e; font-size: 12px;">Result</div>
          <span class="badge" :class="info.evaluation.resolved ? 'badge-green' : 'badge-red'">
            {{ info.evaluation.resolved ? 'RESOLVED' : 'FAIL' }}
          </span>
        </div>
        <div v-if="info.evaluation">
          <div style="color: #8b949e; font-size: 12px;">F2P</div>
          <strong>{{ info.evaluation.f2p || '-' }}</strong>
        </div>
        <div v-if="info.evaluation">
          <div style="color: #8b949e; font-size: 12px;">P2P</div>
          <strong>{{ info.evaluation.p2p || '-' }}</strong>
        </div>
        <div v-if="info.evaluation">
          <div style="color: #8b949e; font-size: 12px;">Duration</div>
          <strong>{{ info.evaluation.duration?.toFixed(1) }}s</strong>
        </div>
        <div>
          <div style="color: #8b949e; font-size: 12px;">Messages</div>
          <strong>{{ messages.length }}</strong>
        </div>
      </div>

      <!-- Problem statement -->
      <div v-if="info.problem_statement" class="card">
        <h3>Problem Statement</h3>
        <pre class="problem-text">{{ info.problem_statement }}</pre>
      </div>

      <!-- Tabs: Messages | Patch | Logs -->
      <div class="card">
        <div class="tabs">
          <button
            v-for="tab in tabs"
            :key="tab.key"
            :class="['tab', { active: activeTab === tab.key }]"
            @click="activeTab = tab.key"
          >{{ tab.label }}</button>
        </div>

        <!-- Messages tab -->
        <div v-if="activeTab === 'messages'" style="margin-top: 16px;">
          <div v-if="msgLoading">Loading messages...</div>
          <div v-else-if="messages.length === 0" style="color: #8b949e;">
            No messages extracted. The agent output may not be in a recognized format.
          </div>
          <MessageList v-else :messages="messages" />
        </div>

        <!-- Patch tab -->
        <div v-if="activeTab === 'patch'" style="margin-top: 16px;">
          <pre class="code-block" v-if="patchContent">{{ patchContent }}</pre>
          <div v-else style="color: #8b949e;">No patch available.</div>
        </div>

        <!-- Logs tab -->
        <div v-if="activeTab === 'logs'" style="margin-top: 16px;">
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
    fmtSize,
    agentBadge,
  },
}
</script>

<style scoped>
.problem-text {
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
  color: #c9d1d9;
  background: #0d1117;
  padding: 16px;
  border-radius: 6px;
  max-height: 200px;
  overflow-y: auto;
}
.code-block {
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-size: 12px;
  line-height: 1.5;
  white-space: pre-wrap;
  color: #c9d1d9;
  background: #0d1117;
  padding: 16px;
  border-radius: 6px;
  max-height: 600px;
  overflow-y: auto;
}
.tabs {
  display: flex;
  gap: 4px;
  border-bottom: 1px solid #30363d;
  padding-bottom: 0;
}
.tab {
  background: none;
  border: none;
  color: #8b949e;
  padding: 8px 16px;
  font-size: 13px;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: color 0.15s, border-color 0.15s;
}
.tab:hover { color: #e1e4e8; }
.tab.active {
  color: #58a6ff;
  border-bottom-color: #58a6ff;
}
.log-files {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 12px;
}
.log-file-btn {
  background: #21262d;
  border: 1px solid #30363d;
  color: #c9d1d9;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
}
.log-file-btn:hover { border-color: #58a6ff; }
.log-file-btn.active { border-color: #58a6ff; background: #1a2d4a; }
</style>
