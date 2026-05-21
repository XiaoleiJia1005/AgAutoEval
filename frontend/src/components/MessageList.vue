<template>
  <div class="message-list">
    <div
      v-for="(msg, i) in messages"
      :key="i"
      :class="['message', `role-${msg.role}`]"
    >
      <div class="msg-header">
        <span class="msg-role">{{ msg.role }}</span>
        <span v-if="msg.metadata?.step" class="msg-step">Step {{ msg.metadata.step }}</span>
        <span v-if="msg.timestamp" class="msg-time">{{ msg.timestamp }}</span>
      </div>
      <div class="msg-body">
        <pre class="msg-content">{{ msg.content }}</pre>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'MessageList',
  props: {
    messages: { type: Array, required: true },
  },
}
</script>

<style scoped>
.message-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.message {
  border-radius: 6px;
  overflow: hidden;
  border-left: 3px solid #30363d;
}
.msg-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: #21262d;
  font-size: 12px;
}
.msg-role {
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-size: 11px;
}
.msg-step {
  color: #58a6ff;
  font-size: 11px;
}
.msg-time {
  color: #8b949e;
  margin-left: auto;
  font-size: 11px;
}
.msg-body {
  padding: 12px;
}
.msg-content {
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-size: 12px;
  line-height: 1.5;
  white-space: pre-wrap;
  color: #c9d1d9;
  margin: 0;
  max-height: 500px;
  overflow-y: auto;
}

/* Role colors */
.role-user { border-left-color: #58a6ff; }
.role-user .msg-role { color: #58a6ff; }
.role-assistant { border-left-color: #3fb950; }
.role-assistant .msg-role { color: #3fb950; }
.role-tool_call { border-left-color: #d29922; }
.role-tool_call .msg-role { color: #d29922; }
.role-tool_result { border-left-color: #a371f7; }
.role-tool_result .msg-role { color: #a371f7; }
.role-thinking { border-left-color: #8b949e; }
.role-thinking .msg-role { color: #8b949e; }
.role-agent { border-left-color: #79c0ff; }
.role-agent .msg-role { color: #79c0ff; }
.role-system { border-left-color: #f85149; }
.role-system .msg-role { color: #f85149; }
</style>
