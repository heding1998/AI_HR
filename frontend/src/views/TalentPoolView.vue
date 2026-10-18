<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { listTalentPool, type TalentPoolEntry } from '../api/talentPool'

const pool = ref<TalentPoolEntry[]>([])
const selectedTier = ref<string>('') // '' = 全部分级
const loading = ref(false)

const TIERS = ['一般优秀', '中等优秀', '特别优秀']

function tierClass(tier: string): string {
  if (tier === '特别优秀') return 'tier-high'
  if (tier === '中等优秀') return 'tier-mid'
  return 'tier-low'
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

onMounted(loadPool)
</script>

<template>
  <div class="pool">
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
          <template #default="{ row }">
            <span class="score-num">{{ row.score }}</span>
          </template>
        </el-table-column>
        <el-table-column label="分级" width="140">
          <template #default="{ row }">
            <span class="tier-badge" :class="tierClass(row.tier)">{{ row.tier }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="入库时间" width="180" />
      </el-table>
    </el-card>
  </div>
</template>

<style scoped>
.toolbar {
  margin-bottom: 16px;
}

.label {
  margin-right: 8px;
  color: var(--ink-3);
}

.tier-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 4px;
  font-size: 12px;
  line-height: 20px;
}

.tier-low {
  color: var(--ink-3);
  background: var(--el-border-color-extra-light);
}

.tier-mid {
  color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
}

.tier-high {
  color: var(--amber);
  background: rgba(183, 121, 31, 0.12);
  font-weight: 600;
}
</style>
