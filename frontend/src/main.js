import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import RunsView from './views/RunsView.vue'
import RunDetail from './views/RunDetail.vue'
import InstanceDetail from './views/InstanceDetail.vue'
import AgentList from './views/AgentList.vue'
import AgentDetail from './views/AgentDetail.vue'

const routes = [
  { path: '/', name: 'runs', component: RunsView },
  { path: '/run/:runId', name: 'run-detail', component: RunDetail, props: true },
  { path: '/run/:runId/instance/:instanceId', name: 'instance-detail', component: InstanceDetail, props: true },
  { path: '/agents', name: 'agents', component: AgentList },
  { path: '/agents/:agentId', name: 'agent-detail', component: AgentDetail, props: true },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

const app = createApp(App)
app.use(router)
app.mount('#app')
