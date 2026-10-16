<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { clearToken } from '../api/auth'
import { listTalentPool, type TalentPoolEntry } from '../api/talentPool'

const router = useRouter()

const pool = ref<TalentPoolEntry[]>([])
const selectedTier = ref<string>('') // '' = 全部分级
const loading = ref(false)

const TIERS = ['一般优秀', '中等优秀', '特别优秀']

const tierMap: Record<string, { type: string }> = {
  一般优秀: { type: 'info' },
  中等优秀: { type: 'warning' },
  特别优秀: { type: 'success' },
}

async function loadPool() {
  loading.value = true
  try {
    pool.value = await listTalentPool(selectedTier.value || undefined)
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : '加载失败')
  } finally {
    loading.value = false
  }
}

function onLogout() {
  clearToken()
  router.push({ name: 'login' })
}

onMounted(loadPool)
</script>

<template>
  <div class="pool">
    <header class="bar">
      <h1>高分人才库</h1>
      <div class="actions">
        <el-button @click="router.push({ name: 'home' })">首页</el-button>
        <el-button @click="onLogout">退出登录</el-button>
      </div>
    </header>

    <el-card>
      <div class="toolbar">
        <span class="label">分级：</span>
        <el-select v-model="selectedTier" style="width: 200px" @change="loadPool">
          <el-option label="全部分级" value="" />
          <el-option v-for="t in TIERS" :key="t" :label="t" :value="t" />
        </el-select>
      </div>

      <el-table v-loading="loading" :data="pool">
        <el-table-column prop="name" label="姓名" width="140" />
        <el-table-column prop="contact" label="联系方式" width="180" />
        <el-table-column label="分数" width="120" sortable>
          <template #default="{ row }">{{ row.score }}</template>
        </el-table-column>
        <el-table-column label="分级" width="140">
          <template #default="{ row }">
            <el-tag :type="tierMap[row.tier]?.type ?? 'info'">{{ row.tier }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="入库时间" width="180" />
      </el-table>
    </el-card>
  </div>
</template>

<style scoped>
.pool {
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

.toolbar {
  margin-bottom: 16px;
}

.label {
  margin-right: 8px;
}
</style>
