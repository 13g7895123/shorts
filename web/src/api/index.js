import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export default {
  // 系統狀態
  getHealth() {
    return api.get('/health')
  },

  // 影片管理
  getVideos(params) {
    return api.get('/videos', { params })
  },
  
  getVideo(id) {
    return api.get(`/videos/${id}`)
  },
  
  updateVideo(id, data) {
    return api.put(`/videos/${id}`, data)
  },
  
  deleteVideo(id) {
    return api.delete(`/videos/${id}`)
  },

  // 爆款發現
  discoverViral(params) {
    return api.post('/discover/viral', params)
  },
  
  addUrl(url) {
    return api.post('/discover/url', { url })
  },
  
  batchImport(data) {
    return api.post('/discover/batch', data)
  },

  // AI 分析
  analyzeVideo(id) {
    return api.post(`/analysis/video/${id}`)
  },
  
  batchAnalyze(params) {
    return api.post('/analysis/batch', params)
  },
  
  getAnalysis(id) {
    return api.get(`/analysis/${id}`)
  },

  // 分類
  classifyVideo(id, category) {
    return api.post(`/classify/${id}`, { category })
  },
  
  batchClassify() {
    return api.post('/classify/batch')
  },

  // 元數據生成
  generateMetadata(videoId, params) {
    return api.post(`/metadata/generate/${videoId}`, params)
  },

  // 排程管理
  getSchedules(params) {
    return api.get('/schedule', { params })
  },
  
  addSchedule(data) {
    return api.post('/schedule', data)
  },
  
  updateSchedule(id, data) {
    return api.put(`/schedule/${id}`, data)
  },
  
  deleteSchedule(id) {
    return api.delete(`/schedule/${id}`)
  },
  
  getScheduleStats() {
    return api.get('/schedule/stats')
  },

  // 上傳
  uploadVideo(formData) {
    return api.post('/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  // 統計
  getStats() {
    return api.get('/stats')
  },
}
