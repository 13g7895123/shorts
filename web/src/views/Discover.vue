<template>
  <div class="discover">
    <h2 class="page-title">爆款發現</h2>

    <div class="grid grid-2">
      <div class="card">
        <h3>🔍 自動發現</h3>
        <p>從熱門頻道自動發現爆款 Shorts</p>
        
        <div class="form-group">
          <label>最小觀看數</label>
          <input v-model.number="autoDiscover.min_views" type="number" class="input" />
        </div>
        
        <div class="form-group">
          <label>影片數量</label>
          <input v-model.number="autoDiscover.limit" type="number" class="input" />
        </div>
        
        <button class="btn btn-primary" @click="startAutoDiscover" :disabled="discovering">
          {{ discovering ? '發現中...' : '開始發現' }}
        </button>
      </div>

      <div class="card">
        <h3>➕ 手動添加</h3>
        <p>直接添加 YouTube Shorts URL</p>
        
        <div class="form-group">
          <label>YouTube URL</label>
          <input 
            v-model="manualUrl" 
            type="text" 
            class="input" 
            placeholder="https://youtube.com/shorts/..."
          />
        </div>
        
        <button class="btn btn-success" @click="addManualUrl" :disabled="!manualUrl">
          添加影片
        </button>
      </div>
    </div>

    <div class="card">
      <h3>📦 批量導入</h3>
      <p>從 CSV 或 JSON 文件批量導入影片 URL</p>
      
      <div class="upload-area" @click="triggerFileInput">
        <input 
          ref="fileInput" 
          type="file" 
          accept=".csv,.json" 
          @change="handleFileUpload"
          style="display: none"
        />
        <div class="upload-icon">📁</div>
        <div>點擊選擇文件 (CSV 或 JSON)</div>
        <div v-if="selectedFile" class="selected-file">
          已選擇: {{ selectedFile.name }}
        </div>
      </div>
      
      <button 
        v-if="selectedFile" 
        class="btn btn-primary" 
        @click="batchImport"
        :disabled="importing"
      >
        {{ importing ? '導入中...' : '開始導入' }}
      </button>
    </div>

    <div v-if="results.length > 0" class="card">
      <h3>發現結果 ({{ results.length }})</h3>
      <table class="table">
        <thead>
          <tr>
            <th>縮圖</th>
            <th>標題</th>
            <th>頻道</th>
            <th>觀看數</th>
            <th>讚數</th>
            <th>時長</th>
            <th>狀態</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="video in results" :key="video.url">
            <td>
              <img :src="video.thumbnail" alt="" class="thumbnail" />
            </td>
            <td>{{ video.title }}</td>
            <td>{{ video.channel }}</td>
            <td>{{ formatNumber(video.views) }}</td>
            <td>{{ formatNumber(video.likes) }}</td>
            <td>{{ video.duration }}</td>
            <td>
              <span class="badge badge-success">✓ 已添加</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import api from '@/api'

const discovering = ref(false)
const importing = ref(false)
const autoDiscover = ref({
  min_views: 100000,
  limit: 10,
})
const manualUrl = ref('')
const selectedFile = ref(null)
const fileInput = ref(null)
const results = ref([])

async function startAutoDiscover() {
  try {
    discovering.value = true
    const data = await api.discoverViral(autoDiscover.value)
    results.value = data.videos || []
    alert(`成功發現 ${results.value.length} 個爆款影片！`)
  } catch (error) {
    alert('發現失敗：' + error.message)
  } finally {
    discovering.value = false
  }
}

async function addManualUrl() {
  try {
    await api.addUrl(manualUrl.value)
    alert('影片已成功添加！')
    manualUrl.value = ''
  } catch (error) {
    alert('添加失敗：' + error.message)
  }
}

function triggerFileInput() {
  fileInput.value.click()
}

function handleFileUpload(event) {
  selectedFile.value = event.target.files[0]
}

async function batchImport() {
  if (!selectedFile.value) return
  
  try {
    importing.value = true
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    
    await api.batchImport(formData)
    alert('批量導入成功！')
    selectedFile.value = null
    fileInput.value.value = ''
  } catch (error) {
    alert('導入失敗：' + error.message)
  } finally {
    importing.value = false
  }
}

function formatNumber(num) {
  if (!num) return '-'
  return num.toLocaleString()
}
</script>

<style scoped>
.page-title {
  margin-bottom: 2rem;
  font-size: 2rem;
  color: #1f2937;
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

.upload-area {
  border: 2px dashed #d1d5db;
  border-radius: 8px;
  padding: 3rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  margin-bottom: 1rem;
}

.upload-area:hover {
  border-color: #667eea;
  background: #f9fafb;
}

.upload-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.selected-file {
  margin-top: 1rem;
  color: #667eea;
  font-weight: 600;
}

.thumbnail {
  width: 80px;
  height: 45px;
  object-fit: cover;
  border-radius: 4px;
}
</style>
