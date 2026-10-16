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
      <div class="actions">
        <el-button @click="router.push({ name: 'jobs' })">岗位管理</el-button>
        <el-button @click="onLogout">退出登录</el-button>
      </div>
    </header>
    <p>欢迎使用 AI HR 智能招聘平台</p>
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

.actions {
  display: flex;
  gap: 8px;
}
</style>
