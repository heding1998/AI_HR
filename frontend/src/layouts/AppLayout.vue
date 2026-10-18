<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { clearToken } from '../api/auth'

const route = useRoute()
const router = useRouter()

const nav = [
  { name: 'home', label: '首页' },
  { name: 'jobs', label: '岗位管理' },
  { name: 'scoring-standard', label: '评分标准' },
  { name: 'batches', label: '简历上传' },
  { name: 'applications', label: '评分结果' },
  { name: 'talent-pool', label: '高分人才库' },
]

const pageTitle = computed(() => (route.meta.title as string | undefined) ?? 'AI HR')

function onLogout() {
  clearToken()
  router.push({ name: 'login' })
}
</script>

<template>
  <div class="shell">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-mark">AI HR</div>
        <div class="brand-sub">智能招聘平台</div>
      </div>
      <nav class="nav">
        <router-link
          v-for="item in nav"
          :key="item.name"
          :to="{ name: item.name }"
          class="nav-item"
        >
          {{ item.label }}
        </router-link>
      </nav>
    </aside>

    <div class="main">
      <header class="topbar">
        <h1 class="page-title">{{ pageTitle }}</h1>
        <el-button plain size="small" @click="onLogout">退出登录</el-button>
      </header>
      <main class="content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<style scoped>
.shell {
  display: flex;
  min-height: 100vh;
}

.sidebar {
  width: 220px;
  flex-shrink: 0;
  background: var(--ink);
  color: #fff;
  display: flex;
  flex-direction: column;
}

.brand {
  padding: 24px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.brand-mark {
  font-family: var(--font-mono);
  font-size: 20px;
  font-weight: 700;
  letter-spacing: 0.02em;
}

.brand-sub {
  margin-top: 4px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.55);
}

.nav {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.nav-item {
  display: block;
  padding: 10px 14px;
  border-radius: 6px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 14px;
  transition: background 0.15s ease, color 0.15s ease;
}

.nav-item:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.06);
}

.nav-item.router-link-exact-active {
  background: var(--teal);
  color: #fff;
}

.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.topbar {
  height: 56px;
  flex-shrink: 0;
  background: var(--surface);
  border-bottom: 1px solid var(--line);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}

.page-title {
  font-size: 16px;
  font-weight: 600;
}

.content {
  flex: 1;
  padding: 24px;
  overflow: auto;
}
</style>
