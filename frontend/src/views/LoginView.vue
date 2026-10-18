<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { login, setToken } from '../api/auth'

const router = useRouter()
const username = ref('')
const password = ref('')
const loading = ref(false)

async function onSubmit() {
  if (!username.value || !password.value) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    const resp = await login(username.value, password.value)
    setToken(resp.access_token)
    router.push({ name: 'home' })
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-card">
      <div class="brand">
        <div class="brand-mark">AI HR</div>
        <div class="brand-sub">智能招聘平台 · 简历初筛</div>
      </div>

      <el-form class="form" @submit.prevent="onSubmit">
        <el-form-item>
          <el-input
            v-model="username"
            placeholder="用户名"
            size="large"
            autocomplete="username"
          />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="password"
            type="password"
            placeholder="密码"
            size="large"
            autocomplete="current-password"
            show-password
          />
        </el-form-item>
        <el-button
          type="primary"
          native-type="submit"
          size="large"
          class="submit"
          :loading="loading"
        >
          登录
        </el-button>
      </el-form>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: var(--paper);
}

.login-card {
  width: 380px;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 40px 36px 36px;
  box-shadow: 0 10px 30px rgba(27, 34, 51, 0.06);
}

.brand {
  text-align: center;
  margin-bottom: 28px;
}

.brand-mark {
  font-family: var(--font-mono);
  font-size: 30px;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: var(--ink);
}

.brand-sub {
  margin-top: 6px;
  font-size: 13px;
  color: var(--ink-3);
}

.form :deep(.el-form-item) {
  margin-bottom: 20px;
}

.submit {
  width: 100%;
  margin-top: 4px;
}
</style>
