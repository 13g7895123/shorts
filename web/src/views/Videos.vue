<template>
  <div class="videos">
    <div class="page-header">
      <h2 class="page-title">影片管理</h2>
      <div class="actions">
        <button class="btn btn-secondary" @click="showFilters = !showFilters">
          🔍 篩選
        </button>
        <button class="btn btn-primary" @click="refreshVideos">
          🔄 重新整理
        </button>
      </div>
    </div>

    <div v-if="showFilters" class="card filters">
      <div class="grid grid-3">
        <div>
          <label>狀態</label>
          <select v-model="filters.status" class="input">
            <option value="">全部</option>
            <option value="pending">待處理</option>
            <option value="analyzed">已分析</option>
            <option value="classified">已分類</option>
            <option value="scheduled">已排程</option>
            <option value="published">已發布</option>
          </select>
        </div>
        <div>
          <label>分類</label>
          <select v-model="filters.category" class="input">
            <option value="">全部</option>
            <option value="gaming">遊戲</option>
            <option value="comedy">喜劇</option>
            <option value="education">教育</option>
            <option value="tech">科技</option>
            <option value="lifestyle">生活</option>
          </select>
        </div>
        <div>
          <label>搜尋</label>
          <input v-model="filters.search" class="input" placeholder="搜尋標題或描述..." />
        </div>
      </div>
    </div>

    <div class="card">
      <table class="table">
        <thead>
          <tr>
            <th>縮圖</th>
            <th>標題</th>
            <th>分類</th>
            <th>狀態</th>
            <th>觀看數</th>
            <th>時間</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="video in videoStore.videos" :key="video.id">
            <td>
              <img :src="video.thumbnail" :alt="video.title" class="thumbnail" />
            </td>
            <td>
              <div class="video-title">{{ video.title || video.url }}</div>
            </td>
            <td>
              <span v-if="video.category" class="badge badge-info">
                {{ video.category }}
              </span>
            </td>
            <td>
              <span :class="`badge badge-${getStatusColor(video.status)}`">
                {{ getStatusText(video.status) }}
              </span>
            </td>
            <td>{{ formatNumber(video.views) }}</td>
            <td>{{ formatDate(video.created_at) }}</td>
            <td>
              <div class="action-buttons">
                <button class="btn-icon" @click="analyzeVideo(video.id)" title="分析">
                  🤖
                </button>
                <button class="btn-icon" @click="editVideo(video.id)" title="編輯">
                  ✏️
                </button>
                <button class="btn-icon" @click="deleteVideo(video.id)" title="刪除">
                  🗑️
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>

      <div v-if="videoStore.loading" class="loading">載入中...</div>
      <div v-else-if="videoStore.videos.length === 0" class="loading">
        暫無影片資料
      </div>
    </div>

    <div class="pagination">
      <button class="btn btn-secondary" :disabled="currentPage === 1" @click="prevPage">
        上一頁
      </button>
      <span>第 {{ currentPage }} 頁</span>
      <button class="btn btn-secondary" @click="nextPage">下一頁</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useVideoStore } from '@/stores/video'
import api from '@/api'

const videoStore = useVideoStore()
const showFilters = ref(false)
const currentPage = ref(1)
const filters = ref({
  status: '',
  category: '',
  search: '',
})

onMounted(() => {
  refreshVideos()
})

watch(filters, () => {
  currentPage.value = 1
  refreshVideos()
}, { deep: true })

function refreshVideos() {
  videoStore.fetchVideos({
    page: currentPage.value,
    ...filters.value,
  })
}

function prevPage() {
  if (currentPage.value > 1) {
    currentPage.value--
    refreshVideos()
  }
}

function nextPage() {
  currentPage.value++
  refreshVideos()
}

async function analyzeVideo(id) {
  try {
    await api.analyzeVideo(id)
    alert('分析已開始')
    refreshVideos()
  } catch (error) {
    alert('分析失敗：' + error.message)
  }
}

function editVideo(id) {
  // TODO: 實作編輯功能
  console.log('Edit video:', id)
}

async function deleteVideo(id) {
  if (confirm('確定要刪除這個影片嗎？')) {
    await videoStore.deleteVideo(id)
  }
}

function getStatusColor(status) {
  const colors = {
    pending: 'warning',
    analyzed: 'info',
    classified: 'info',
    scheduled: 'success',
    published: 'success',
  }
  return colors[status] || 'warning'
}

function getStatusText(status) {
  const texts = {
    pending: '待處理',
    analyzed: '已分析',
    classified: '已分類',
    scheduled: '已排程',
    published: '已發布',
  }
  return texts[status] || status
}

function formatNumber(num) {
  if (!num) return '-'
  return num.toLocaleString()
}

function formatDate(date) {
  if (!date) return '-'
  return new Date(date).toLocaleString('zh-TW')
}
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.page-title {
  font-size: 2rem;
  color: #1f2937;
  margin: 0;
}

.actions {
  display: flex;
  gap: 1rem;
}

.filters {
  margin-bottom: 1.5rem;
}

.filters label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 600;
  color: #374151;
}

.thumbnail {
  width: 80px;
  height: 45px;
  object-fit: cover;
  border-radius: 4px;
}

.video-title {
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.action-buttons {
  display: flex;
  gap: 0.5rem;
}

.btn-icon {
  background: none;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
  padding: 0.25rem;
  transition: transform 0.2s;
}

.btn-icon:hover {
  transform: scale(1.2);
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  margin-top: 2rem;
}
</style>
