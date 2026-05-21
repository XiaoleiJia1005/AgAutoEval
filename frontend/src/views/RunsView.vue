<template>
  <div>
    <h2>Evaluation Runs</h2>
    <p style="color: #8b949e; margin-bottom: 20px;">
      Data directory: <code class="mono">{{ baseDir }}</code>
    </p>

    <div v-if="loading" style="color: #8b949e;">Loading...</div>
    <div v-else-if="error" class="card" style="color: #f85149;">{{ error }}</div>

    <table v-else-if="runs.length">
      <thead>
        <tr>
          <th>Run ID</th>
          <th>Agent</th>
          <th>Instances</th>
          <th>Resolved</th>
          <th>Accuracy</th>
          <th>Duration</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="run in runs" :key="run.run_id">
          <td>
            <router-link :to="`/run/${run.run_id}`" class="link mono">
              {{ run.run_id }}
            </router-link>
          </td>
          <td>
            <span class="badge" :class="agentBadge(run.agent_type)">
              {{ run.agent_type }}
            </span>
          </td>
          <td>{{ run.instance_count }}</td>
          <td>{{ run.resolved ?? '-' }} / {{ run.total ?? '-' }}</td>
          <td>
            <span v-if="run.accuracy != null">
              {{ (run.accuracy * 100).toFixed(1) }}%
            </span>
            <span v-else>-</span>
          </td>
          <td>{{ formatDuration(run.total_duration) }}</td>
          <td>
            <router-link :to="`/run/${run.run_id}`" class="link">View</router-link>
          </td>
        </tr>
      </tbody>
    </table>

    <div v-else class="card" style="color: #8b949e; text-align: center; padding: 40px;">
      No evaluation runs found.<br/>
      Run <code class="mono">python -m agautoeval config.yaml</code> to get started.
    </div>
  </div>
</template>

<script>
import { getRuns } from '../api.js'
import { formatDuration, agentBadge } from '../utils.js'

export default {
  name: 'RunsView',
  data() {
    return { runs: [], baseDir: '', loading: true, error: '' }
  },
  async created() {
    try {
      const data = await getRuns()
      this.runs = data.runs
      this.baseDir = data.base_dir
    } catch (e) {
      this.error = `Failed to load runs: ${e.message}`
    } finally {
      this.loading = false
    }
  },
  methods: { formatDuration, agentBadge },
}
</script>
