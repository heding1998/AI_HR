<script setup lang="ts">
import { useRouter } from 'vue-router'
import { clearToken } from '../api/auth'

const router = useRouter()

function onLogout() {
  clearToken()
  router.push({ name: 'login' })
}
</script>

<template>
  <div class="home">
    <header class="bar">
      <h1>AI HR 智能招聘平台</h1>
      <el-button @click="onLogout">退出登录</el-button>
    </header>
    <p>已登录，功能建设中</p>
  </div>
</template>

<style scoped>
.home {
  padding: 24px;
}

.bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
</style>
