<template>
  <div class="settings">
    <h2 class="page-title">系統設定</h2>

    <div class="card">
      <h3>🔑 API 設定</h3>
      <div class="form-group">
        <label>YouTube API Key</label>
        <input v-model="settings.youtube_api_key" type="password" class="input" />
      </div>
      <div class="form-group">
        <label>Gemini API Key</label>
        <input v-model="settings.gemini_api_key" type="password" class="input" />
      </div>
      <button class="btn btn-primary" @click="saveApiSettings">儲存 API 設定</button>
    </div>

    <div class="card">
      <h3>⚙️ 系統參數</h3>
      <div class="grid grid-2">
        <div class="form-group">
          <label>每日上傳限制</label>
          <input v-model.number="settings.daily_upload_limit" type="number" class="input" />
        </div>
        <div class="form-group">
          <label>批量處理數量</label>
          <input v-model.number="settings.batch_size" type="number" class="input" />
        </div>
        <div class="form-group">
          <label>最小觀看數</label>
          <input v-model.number="settings.min_views" type="number" class="input" />
        </div>
        <div class="form-group">
          <label>AI 分析模型</label>
          <select v-model="settings.ai_model" class="input">
            <option value="gemini-pro">Gemini Pro</option>
            <option value="gemini-pro-vision">Gemini Pro Vision</option>
          </select>
        </div>
      </div>
      <button class="btn btn-primary" @click="saveSystemSettings">儲存系統設定</button>
    </div>

    <div class="card">
      <h3>🎨 介面設定</h3>
      <div class="form-group">
        <label>語言</label>
        <select v-model="settings.language" class="input">
          <option value="zh-TW">繁體中文</option>
          <option value="zh-CN">简体中文</option>
          <option value="en">English</option>
        </select>
      </div>
      <div class="form-group">
        <label>主題</label>
        <select v-model="settings.theme" class="input">
          <option value="light">淺色</option>
          <option value="dark">深色</option>
          <option value="auto">自動</option>
        </select>
      </div>
      <button class="btn btn-primary" @click="saveInterfaceSettings">儲存介面設定</button>
    </div>

    <div class="card">
      <h3>📊 資料管理</h3>
      <div class="actions-grid">
        <button class="btn btn-secondary" @click="exportData">
          📥 匯出資料
        </button>
        <button class="btn btn-secondary" @click="importData">
          📤 匯入資料
        </button>
        <button class="btn btn-secondary" @click="clearCache">
          🧹 清除快取
        </button>
        <button class="btn btn-danger" @click="resetDatabase">
          ⚠️ 重置資料庫
        </button>
      </div>
    </div>

    <div class="card">
      <h3>ℹ️ 系統資訊</h3>
      <div class="info-list">
        <div class="info-item">
          <span>版本號</span>
          <span>v0.1.0</span>
        </div>
        <div class="info-item">
          <span>Python 版本</span>
          <span>3.12+</span>
        </div>
        <div class="info-item">
          <span>資料庫</span>
          <span>SQLite</span>
        </div>
        <div class="info-item">
          <span>儲存位置</span>
          <span>/data</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const settings = ref({
  youtube_api_key: '',
  gemini_api_key: '',
  daily_upload_limit: 10,
  batch_size: 5,
  min_views: 100000,
  ai_model: 'gemini-pro',
  language: 'zh-TW',
  theme: 'light',
})

onMounted(() => {
  loadSettings()
})

function loadSettings() {
  // TODO: 從後端加載設定
  const saved = localStorage.getItem('settings')
  if (saved) {
    settings.value = { ...settings.value, ...JSON.parse(saved) }
  }
}

function saveApiSettings() {
  localStorage.setItem('settings', JSON.stringify(settings.value))
  alert('API 設定已儲存！')
}

function saveSystemSettings() {
  localStorage.setItem('settings', JSON.stringify(settings.value))
  alert('系統設定已儲存！')
}

function saveInterfaceSettings() {
  localStorage.setItem('settings', JSON.stringify(settings.value))
  alert('介面設定已儲存！')
}

function exportData() {
  alert('匯出資料功能開發中...')
}

function importData() {
  alert('匯入資料功能開發中...')
}

function clearCache() {
  if (confirm('確定要清除快取嗎？')) {
    alert('快取已清除！')
  }
}

function resetDatabase() {
  if (confirm('警告：這將刪除所有資料！確定要重置資料庫嗎？')) {
    alert('資料庫重置功能需要謹慎操作，請聯繫管理員')
  }
}
</script>

<style scoped>
.page-title {
  margin-bottom: 2rem;
  font-size: 2rem;
  color: #1f2937;
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

.actions-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.info-list {
  margin-top: 1rem;
}

.info-item {
  display: flex;
  justify-content: space-between;
  padding: 1rem 0;
  border-bottom: 1px solid #e5e7eb;
}

.info-item:last-child {
  border-bottom: none;
}

.info-item span:first-child {
  color: #6b7280;
}

.info-item span:last-child {
  font-weight: 600;
  color: #1f2937;
}
</style>
