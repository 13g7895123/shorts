<template>
  <div id="app">
    <nav class="navbar">
      <div class="container">
        <h1 class="logo">🎬 YouTube Shorts 管理系統</h1>
        <div class="nav-links">
          <router-link to="/">儀表板</router-link>
          <router-link to="/videos">影片管理</router-link>
          <router-link to="/discover">爆款發現</router-link>
          <router-link to="/analysis">AI 分析</router-link>
          <router-link to="/schedule">排程管理</router-link>
          <router-link to="/settings">設定</router-link>
        </div>
      </div>
    </nav>
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useSystemStore } from '@/stores/system'

const systemStore = useSystemStore()

onMounted(() => {
  systemStore.checkHealth()
})
</script>

<style scoped>
.navbar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 1rem 0;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logo {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 700;
}

.nav-links {
  display: flex;
  gap: 2rem;
}

.nav-links a {
  color: white;
  text-decoration: none;
  font-weight: 500;
  transition: opacity 0.3s;
}

.nav-links a:hover,
.nav-links a.router-link-active {
  opacity: 0.8;
  border-bottom: 2px solid white;
}

.main-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
}
</style>
