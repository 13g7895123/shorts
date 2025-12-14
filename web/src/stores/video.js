import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api'

export const useVideoStore = defineStore('video', () => {
  const videos = ref([])
  const currentVideo = ref(null)
  const loading = ref(false)
  const total = ref(0)

  async function fetchVideos(params = {}) {
    try {
      loading.value = true
      const data = await api.getVideos(params)
      videos.value = data.videos || []
      total.value = data.total || 0
    } catch (error) {
      console.error('Failed to fetch videos:', error)
    } finally {
      loading.value = false
    }
  }

  async function fetchVideo(id) {
    try {
      loading.value = true
      currentVideo.value = await api.getVideo(id)
    } catch (error) {
      console.error('Failed to fetch video:', error)
    } finally {
      loading.value = false
    }
  }

  async function updateVideo(id, data) {
    try {
      loading.value = true
      await api.updateVideo(id, data)
      await fetchVideos()
    } catch (error) {
      console.error('Failed to update video:', error)
    } finally {
      loading.value = false
    }
  }

  async function deleteVideo(id) {
    try {
      loading.value = true
      await api.deleteVideo(id)
      await fetchVideos()
    } catch (error) {
      console.error('Failed to delete video:', error)
    } finally {
      loading.value = false
    }
  }

  return {
    videos,
    currentVideo,
    loading,
    total,
    fetchVideos,
    fetchVideo,
    updateVideo,
    deleteVideo,
  }
})
