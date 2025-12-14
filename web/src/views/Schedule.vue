<template>
  <div class="schedule">
    <div class="page-header">
      <h2 class="page-title">排程管理</h2>
      <button class="btn btn-primary" @click="showAddModal = true">
        ➕ 新增排程
      </button>
    </div>

    <div class="grid grid-3">
      <div class="stat-card">
        <div class="stat-icon">📅</div>
        <div class="stat-content">
          <div class="stat-value">{{ scheduleStats.total }}</div>
          <div class="stat-label">總排程</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">⏰</div>
        <div class="stat-content">
          <div class="stat-value">{{ scheduleStats.pending }}</div>
          <div class="stat-label">待執行</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">✅</div>
        <div class="stat-content">
          <div class="stat-value">{{ scheduleStats.completed }}</div>
          <div class="stat-label">已完成</div>
        </div>
      </div>
    </div>

    <div class="card">
      <h3>排程列表</h3>
      <table class="table">
        <thead>
          <tr>
            <th>影片</th>
            <th>平台</th>
            <th>排程時間</th>
            <th>狀態</th>
            <th>優先級</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in schedules" :key="item.id">
            <td>
              <div class="video-info">
                <img :src="item.thumbnail" alt="" class="thumbnail" />
                <span>{{ item.title }}</span>
              </div>
            </td>
            <td>
              <span class="badge badge-info">{{ item.platform }}</span>
            </td>
            <td>{{ formatDateTime(item.scheduled_time) }}</td>
            <td>
              <span :class="`badge badge-${getStatusColor(item.status)}`">
                {{ getStatusText(item.status) }}
              </span>
            </td>
            <td>
              <span :class="`priority priority-${item.priority}`">
                {{ getPriorityText(item.priority) }}
              </span>
            </td>
            <td>
              <div class="action-buttons">
                <button class="btn-icon" @click="editSchedule(item)" title="編輯">
                  ✏️
                </button>
                <button class="btn-icon" @click="deleteSchedule(item.id)" title="刪除">
                  🗑️
                </button>
                <button 
                  v-if="item.status === 'pending'" 
                  class="btn-icon" 
                  @click="executeNow(item.id)" 
                  title="立即執行"
                >
                  ▶️
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 新增排程彈窗 -->
    <div v-if="showAddModal" class="modal" @click="showAddModal = false">
      <div class="modal-content" @click.stop>
        <h3>新增排程</h3>
        <form @submit.prevent="addSchedule">
          <div class="form-group">
            <label>選擇影片</label>
            <select v-model="newSchedule.video_id" class="input" required>
              <option value="">請選擇...</option>
              <option v-for="video in availableVideos" :key="video.id" :value="video.id">
                {{ video.title }}
              </option>
            </select>
          </div>

          <div class="form-group">
            <label>發布平台</label>
            <select v-model="newSchedule.platform" class="input" required>
              <option value="youtube">YouTube</option>
              <option value="tiktok">TikTok</option>
              <option value="instagram">Instagram</option>
            </select>
          </div>

          <div class="form-group">
            <label>排程時間</label>
            <input 
              v-model="newSchedule.scheduled_time" 
              type="datetime-local" 
              class="input" 
              required
            />
          </div>

          <div class="form-group">
            <label>優先級</label>
            <select v-model="newSchedule.priority" class="input">
              <option value="low">低</option>
              <option value="normal">普通</option>
              <option value="high">高</option>
            </select>
          </div>

          <div class="modal-actions">
            <button type="button" class="btn btn-secondary" @click="showAddModal = false">
              取消
            </button>
            <button type="submit" class="btn btn-primary">確定</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api'

const scheduleStats = ref({
  total: 0,
  pending: 0,
  completed: 0,
})

const schedules = ref([])
const availableVideos = ref([])
const showAddModal = ref(false)
const newSchedule = ref({
  video_id: '',
  platform: 'youtube',
  scheduled_time: '',
  priority: 'normal',
})

onMounted(async () => {
  await loadSchedules()
  await loadStats()
})

async function loadSchedules() {
  try {
    const data = await api.getSchedules()
    schedules.value = data.schedules || []
  } catch (error) {
    console.error('Failed to load schedules:', error)
  }
}

async function loadStats() {
  try {
    const data = await api.getScheduleStats()
    scheduleStats.value = data
  } catch (error) {
    console.error('Failed to load stats:', error)
  }
}

async function addSchedule() {
  try {
    await api.addSchedule(newSchedule.value)
    alert('排程已新增！')
    showAddModal.value = false
    resetForm()
    await loadSchedules()
  } catch (error) {
    alert('新增失敗：' + error.message)
  }
}

async function editSchedule(item) {
  // TODO: 實作編輯功能
  console.log('Edit schedule:', item)
}

async function deleteSchedule(id) {
  if (confirm('確定要刪除這個排程嗎？')) {
    try {
      await api.deleteSchedule(id)
      await loadSchedules()
    } catch (error) {
      alert('刪除失敗：' + error.message)
    }
  }
}

async function executeNow(id) {
  if (confirm('確定要立即執行這個排程嗎？')) {
    try {
      // TODO: 實作立即執行
      console.log('Execute now:', id)
    } catch (error) {
      alert('執行失敗：' + error.message)
    }
  }
}

function resetForm() {
  newSchedule.value = {
    video_id: '',
    platform: 'youtube',
    scheduled_time: '',
    priority: 'normal',
  }
}

function getStatusColor(status) {
  const colors = {
    pending: 'warning',
    processing: 'info',
    completed: 'success',
    failed: 'danger',
  }
  return colors[status] || 'info'
}

function getStatusText(status) {
  const texts = {
    pending: '待執行',
    processing: '執行中',
    completed: '已完成',
    failed: '失敗',
  }
  return texts[status] || status
}

function getPriorityText(priority) {
  const texts = {
    low: '低',
    normal: '普通',
    high: '高',
  }
  return texts[priority] || priority
}

function formatDateTime(date) {
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

.video-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.thumbnail {
  width: 80px;
  height: 45px;
  object-fit: cover;
  border-radius: 4px;
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

.priority {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 600;
}

.priority-low {
  background: #e5e7eb;
  color: #6b7280;
}

.priority-normal {
  background: #dbeafe;
  color: #1e40af;
}

.priority-high {
  background: #fee2e2;
  color: #991b1b;
}

.modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  max-width: 600px;
  width: 90%;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 600;
  color: #374151;
}

.modal-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 2rem;
}
</style>
