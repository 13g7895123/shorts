import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api'

export const useSystemStore = defineStore('system', () => {
  const health = ref(null)
  const loading = ref(false)

  async function checkHealth() {
    try {
      loading.value = true
      health.value = await api.getHealth()
    } catch (error) {
      console.error('Health check failed:', error)
    } finally {
      loading.value = false
    }
  }

  return {
    health,
    loading,
    checkHealth,
  }
})
