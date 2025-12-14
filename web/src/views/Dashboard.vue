<template>
  <div class="dashboard">
    <h2 class="page-title">儀表板</h2>
    
    <div class="grid grid-4">
      <div class="stat-card">
        <div class="stat-icon">📹</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.total_videos || 0 }}</div>
          <div class="stat-label">總影片數</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon">✅</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.analyzed || 0 }}</div>
          <div class="stat-label">已分析</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon">📤</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.scheduled || 0 }}</div>
          <div class="stat-label">已排程</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon">🚀</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.published || 0 }}</div>
          <div class="stat-label">已發布</div>
        </div>
      </div>
    </div>

    <div class="grid grid-2">
      <div class="card">
        <h3>快速操作</h3>
        <div class="quick-actions">
          <button class="btn btn-primary" @click="discoverViral">
            🔍 發現爆款
          </button>
          <button class="btn btn-primary" @click="analyzeVideos">
            🤖 批量分析
          </button>
          <button class="btn btn-primary" @click="classifyVideos">
            📁 自動分類
          </button>
          <button class="btn btn-success" @click="generateMetadata">
            ✨ 生成元數據
          </button>
        </div>
      </div>

      <div class="card">
        <h3>系統狀態</h3>
        <div class="status-list">
          <div class="status-item">
            <span>YouTube API</span>
            <span class="badge badge-success">正常</span>
          </div>
          <div class="status-item">
            <span>Gemini AI</span>
            <span class="badge badge-success">正常</span>
          </div>
          <div class="status-item">
            <span>數據庫</span>
            <span class="badge badge-success">正常</span>
          </div>
          <div class="status-item">
            <span>儲存空間</span>
            <span class="badge badge-info">充足</span>
          </div>
        </div>
      </div>
    </div>

    <div class="card">
      <h3>最近活動</h3>
      <div class="activity-list">
        <div v-for="activity in recentActivities" :key="activity.id" class="activity-item">
          <div class="activity-icon">{{ activity.icon }}</div>
          <div class="activity-content">
            <div class="activity-title">{{ activity.title }}</div>
            <div class="activity-time">{{ activity.time }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api'

const router = useRouter()
const stats = ref({
  total_videos: 0,
  analyzed: 0,
  scheduled: 0,
  published: 0,
})

const recentActivities = ref([
  { id: 1, icon: '🔍', title: '發現 5 個爆款影片', time: '10 分鐘前' },
  { id: 2, icon: '🤖', title: '完成 AI 分析 (3/5)', time: '30 分鐘前' },
  { id: 3, icon: '📤', title: '排程上傳 2 個影片', time: '1 小時前' },
  { id: 4, icon: '✅', title: '影片分類完成', time: '2 小時前' },
])

onMounted(async () => {
  try {
    const data = await api.getStats()
    stats.value = data
  } catch (error) {
    console.error('Failed to load stats:', error)
  }
})

function discoverViral() {
  router.push('/discover')
}

function analyzeVideos() {
  router.push('/analysis')
}

function classifyVideos() {
  router.push('/videos')
}

function generateMetadata() {
  router.push('/videos')
}
</script>

<style scoped>
.page-title {
  margin-bottom: 2rem;
  font-size: 2rem;
  color: #1f2937;
}

.stat-card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.stat-icon {
  font-size: 2.5rem;
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: #667eea;
}

.stat-label {
  color: #6b7280;
  font-size: 0.9rem;
}

.quick-actions {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
  margin-top: 1rem;
}

.status-list,
.activity-list {
  margin-top: 1rem;
}

.status-item {
  display: flex;
  justify-content: space-between;
  padding: 0.75rem 0;
  border-bottom: 1px solid #e5e7eb;
}

.status-item:last-child {
  border-bottom: none;
}

.activity-item {
  display: flex;
  gap: 1rem;
  padding: 1rem 0;
  border-bottom: 1px solid #e5e7eb;
}

.activity-item:last-child {
  border-bottom: none;
}

.activity-icon {
  font-size: 1.5rem;
}

.activity-title {
  font-weight: 600;
  color: #1f2937;
}

.activity-time {
  color: #6b7280;
  font-size: 0.85rem;
  margin-top: 0.25rem;
}
</style>
