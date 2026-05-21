<template>
  <div>
    <h2>Evaluation Runs</h2>
    <p style="color: #8b949e; margin-bottom: 20px;">
      Data directory: <code class="mono">{{ baseDir }}</code>
    </p>

    <!-- Filters -->
    <div v-if="runs.length" class="card" style="display: flex; gap: 12px; flex-wrap: wrap; align-items: center; padding: 12px 20px;">
      <span style="color: #8b949e; font-size: 12px; margin-right: 4px;">Filters:</span>
      <select v-model="filterAgent" @change="onFilterChange" class="filter-select">
        <option value="">All Agents</option>
        <option v-for="a in agentOptions" :key="a" :value="a">{{ a }}</option>
      </select>
      <select v-model="filterProvider" @change="onFilterChange" class="filter-select">
        <option value="">All Providers</option>
        <option v-for="p in providerOptions" :key="p" :value="p">{{ p }}</option>
      </select>
      <select v-model="filterModel" @change="onFilterChange" class="filter-select">
        <option value="">All Models</option>
        <option v-for="m in modelOptions" :key="m" :value="m">{{ m }}</option>
      </select>
      <span v-if="filteredRuns.length !== runs.length" style="color: #8b949e; font-size: 12px; margin-left: 8px;">
        {{ filteredRuns.length }} / {{ runs.length }} runs
      </span>
    </div>

    <div v-if="loading" style="color: #8b949e;">Loading...</div>
    <div v-else-if="error" class="card" style="color: #f85149;">{{ error }}</div>

    <table v-else-if="filteredRuns.length">
      <thead>
        <tr>
          <th>Run ID</th>
          <th>Agent</th>
          <th>Provider</th>
          <th>Model</th>
          <th>Instances</th>
          <th>Resolved</th>
          <th class="sortable" @click="toggleSort">
            Accuracy
            <span class="sort-arrow">{{ sortDir === 'desc' ? ' ▼' : sortDir === 'asc' ? ' ▲' : '' }}</span>
          </th>
          <th>Duration</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="run in sortedRuns" :key="run.run_id">
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
          <td>
            <span class="badge" :class="providerBadge(run.provider)">
              {{ run.provider }}
            </span>
          </td>
          <td class="mono" style="max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" :title="run.model">
            {{ run.model || '-' }}
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
      <template v-if="runs.length">No runs match the selected filters.</template>
      <template v-else>
        No evaluation runs found.<br/>
        Run <code class="mono">python -m agautoeval config.yaml</code> to get started.
      </template>
    </div>
  </div>
</template>

<script>
import { getRuns } from '../api.js'
import { formatDuration, agentBadge, providerBadge } from '../utils.js'

export default {
  name: 'RunsView',
  data() {
    return {
      runs: [],
      baseDir: '',
      loading: true,
      error: '',
      filterAgent: '',
      filterProvider: '',
      filterModel: '',
      sortDir: '',  // '', 'asc', 'desc'
    }
  },
  computed: {
    agentOptions() {
      return [...new Set(this.runs.map(r => r.agent_type).filter(Boolean))].sort()
    },
    providerOptions() {
      return [...new Set(this.runs.map(r => r.provider).filter(Boolean))].sort()
    },
    modelOptions() {
      return [...new Set(this.runs.map(r => r.model).filter(Boolean))].sort()
    },
    filteredRuns() {
      let result = this.runs
      if (this.filterAgent) {
        result = result.filter(r => r.agent_type === this.filterAgent)
      }
      if (this.filterProvider) {
        result = result.filter(r => r.provider === this.filterProvider)
      }
      if (this.filterModel) {
        result = result.filter(r => r.model === this.filterModel)
      }
      return result
    },
    sortedRuns() {
      if (!this.sortDir) return this.filteredRuns
      return [...this.filteredRuns].sort((a, b) => {
        const va = a.accuracy ?? -1
        const vb = b.accuracy ?? -1
        return this.sortDir === 'desc' ? vb - va : va - vb
      })
    },
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
  methods: {
    formatDuration,
    agentBadge,
    providerBadge,
    onFilterChange() {
      // Cascade: when agent changes, clear model/provider if they don't match
      if (this.filterAgent && this.modelOptions.indexOf(this.filterModel) === -1) {
        this.filterModel = ''
      }
      if (this.filterAgent && this.providerOptions.indexOf(this.filterProvider) === -1) {
        this.filterProvider = ''
      }
    },
    toggleSort() {
      if (!this.sortDir) this.sortDir = 'desc'
      else if (this.sortDir === 'desc') this.sortDir = 'asc'
      else this.sortDir = ''
    },
  },
}
</script>

<style scoped>
.filter-select {
  background: #21262d;
  border: 1px solid #30363d;
  color: #c9d1d9;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  min-width: 120px;
}
.filter-select:focus {
  outline: none;
  border-color: #58a6ff;
}
.sortable {
  cursor: pointer;
  user-select: none;
}
.sortable:hover {
  color: #58a6ff;
}
.sort-arrow {
  font-size: 10px;
}
</style>
