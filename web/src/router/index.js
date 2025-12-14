import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '@/views/Dashboard.vue'
import Videos from '@/views/Videos.vue'
import Discover from '@/views/Discover.vue'
import Analysis from '@/views/Analysis.vue'
import Schedule from '@/views/Schedule.vue'
import Settings from '@/views/Settings.vue'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard,
  },
  {
    path: '/videos',
    name: 'Videos',
    component: Videos,
  },
  {
    path: '/discover',
    name: 'Discover',
    component: Discover,
  },
  {
    path: '/analysis',
    name: 'Analysis',
    component: Analysis,
  },
  {
    path: '/schedule',
    name: 'Schedule',
    component: Schedule,
  },
  {
    path: '/settings',
    name: 'Settings',
    component: Settings,
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
