<template>
  <div class="analysis">
    <div class="page-header">
      <h2 class="page-title">AI 分析</h2>
      <button class="btn btn-primary" @click="batchAnalyze">
        🤖 批量分析
      </button>
    </div>

    <div class="grid grid-2">
      <div class="card">
        <h3>分析統計</h3>
        <div class="stats-grid">
          <div class="stat-item">
            <div class="stat-number">{{ analysisStats.total }}</div>
            <div class="stat-label">總分析數</div>
          </div>
          <div class="stat-item">
            <div class="stat-number">{{ analysisStats.today }}</div>
            <div class="stat-label">今日分析</div>
          </div>
          <div class="stat-item">
            <div class="stat-number">{{ analysisStats.pending }}</div>
            <div class="stat-label">待分析</div>
          </div>
          <div class="stat-item">
            <div class="stat-number">{{ analysisStats.avg_score }}</div>
            <div class="stat-label">平均評分</div>
          </div>
        </div>
      </div>

      <div class="card">
        <h3>分析設置</h3>
        <div class="form-group">
          <label>分析類型</label>
          <select v-model="settings.analysis_type" class="input">
            <option value="full">完整分析</option>
            <option value="quick">快速分析</option>
            <option value="deep">深度分析</option>
          </select>
        </div>
        <div class="form-group">
          <label>批量數量</label>
          <input v-model.number="settings.batch_size" type="number" class="input" />
        </div>
      </div>
    </div>

    <div class="card">
      <h3>分析結果</h3>
      <table class="table">
        <thead>
          <tr>
            <th>影片</th>
            <th>評分</th>
            <th>關鍵場景</th>
            <th>情緒分析</th>
            <th>建議</th>
            <th>時間</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in analysisResults" :key="item.id">
            <td>
              <div class="video-info">
                <img :src="item.thumbnail" alt="" class="thumbnail" />
                <span>{{ item.title }}</span>
              </div>
            </td>
            <td>
              <div class="score">
                {{ item.score }}/100
                <div class="score-bar">
                  <div class="score-fill" :style="{ width: item.score + '%' }"></div>
                </div>
              </div>
            </td>
            <td>{{ item.scenes_count }} 個</td>
            <td>
              <span :class="`badge badge-${getEmotionColor(item.emotion)}`">
                {{ item.emotion }}
              </span>
            </td>
            <td>
              <button class="btn-icon" @click="showSuggestions(item)" title="查看建議">
                💡
              </button>
            </td>
            <td>{{ formatDate(item.analyzed_at) }}</td>
            <td>
              <button class="btn-icon" @click="viewDetails(item.id)" title="詳情">
                👁️
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 建議彈窗 -->
    <div v-if="showModal" class="modal" @click="closeModal">
      <div class="modal-content" @click.stop>
        <h3>AI 建議</h3>
        <div v-if="selectedItem" class="suggestions">
          <div class="suggestion-item">
            <strong>標題優化：</strong>
            <p>{{ selectedItem.suggestions?.title }}</p>
          </div>
          <div class="suggestion-item">
            <strong>內容改進：</strong>
            <p>{{ selectedItem.suggestions?.content }}</p>
          </div>
          <div class="suggestion-item">
            <strong>發布建議：</strong>
            <p>{{ selectedItem.suggestions?.publishing }}</p>
          </div>
        </div>
        <button class="btn btn-secondary" @click="closeModal">關閉</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api'

const analysisStats = ref({
  total: 0,
  today: 0,
  pending: 0,
  avg_score: 0,
})

const settings = ref({
  analysis_type: 'full',
  batch_size: 5,
})

const analysisResults = ref([])
const showModal = ref(false)
const selectedItem = ref(null)

onMounted(() => {
  loadAnalysisResults()
})

async function loadAnalysisResults() {
  try {
    // TODO: 從 API 加載數據
    analysisResults.value = [
      {
        id: 1,
        thumbnail: 'https://via.placeholder.com/80x45',
        title: '爆款遊戲片段',
        score: 85,
        scenes_count: 5,
        emotion: '興奮',
        analyzed_at: new Date().toISOString(),
        suggestions: {
          title: '建議加入更多關鍵字，提升 SEO',
          content: '開頭 3 秒增加吸引力元素',
          publishing: '建議在晚上 8-10 點發布',
        },
      },
    ]
  } catch (error) {
    console.error('Failed to load analysis results:', error)
  }
}

async function batchAnalyze() {
  try {
    await api.batchAnalyze(settings.value)
    alert('批量分析已開始！')
    loadAnalysisResults()
  } catch (error) {
    alert('分析失敗：' + error.message)
  }
}

function showSuggestions(item) {
  selectedItem.value = item
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  selectedItem.value = null
}

function viewDetails(id) {
  console.log('View details:', id)
}

function getEmotionColor(emotion) {
  const colors = {
    興奮: 'success',
    快樂: 'success',
    驚訝: 'info',
    平靜: 'info',
    緊張: 'warning',
  }
  return colors[emotion] || 'info'
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

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.5rem;
  margin-top: 1rem;
}

.stat-item {
  text-align: center;
}

.stat-number {
  font-size: 2rem;
  font-weight: 700;
  color: #667eea;
}

.stat-label {
  color: #6b7280;
  font-size: 0.9rem;
  margin-top: 0.25rem;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 600;
  color: #374151;
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

.score {
  font-weight: 600;
}

.score-bar {
  width: 100px;
  height: 6px;
  background: #e5e7eb;
  border-radius: 3px;
  margin-top: 0.25rem;
  overflow: hidden;
}

.score-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea, #764ba2);
  transition: width 0.3s;
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

.suggestions {
  margin: 1.5rem 0;
}

.suggestion-item {
  margin-bottom: 1.5rem;
}

.suggestion-item strong {
  color: #667eea;
}

.suggestion-item p {
  margin-top: 0.5rem;
  color: #4b5563;
}
</style>
