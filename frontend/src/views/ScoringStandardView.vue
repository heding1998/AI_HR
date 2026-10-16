<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { clearToken } from '../api/auth'
import { listJobs, type Job } from '../api/jobs'
import {
  getScoringStandard,
  saveStandardA,
  saveStandardB,
  type StandardARow,
  type StandardBRow,
} from '../api/scoringStandard'

const router = useRouter()
const route = useRoute()

const jobs = ref<Job[]>([])
const selectedJobId = ref<number | null>(null)
const activeTab = ref<'a' | 'b'>('a')

const aRows = ref<StandardARow[]>([])
const bRows = ref<StandardBRow[]>([])
const loading = ref(false)
const saving = ref(false)

const categoryTotal = computed(() => {
  const seen = new Set<string>()
  let total = 0
  for (const r of aRows.value) {
    if (!seen.has(r.category)) {
      seen.add(r.category)
      total += r.category_score
    }
  }
  return total
})

async function loadStandard() {
  if (selectedJobId.value === null) return
  loading.value = true
  try {
    const data = await getScoringStandard(selectedJobId.value)
    aRows.value = data.a.map((r) => ({ ...r }))
    bRows.value = data.b.map((r) => ({ ...r }))
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : '加载失败')
  } finally {
    loading.value = false
  }
}

function onJobChange() {
  loadStandard()
}

function addARow() {
  aRows.value.push({ category: '', subcategory: '', category_score: 0, subcategory_score: 0 })
}

function removeARow(index: number) {
  aRows.value.splice(index, 1)
}

function addBRow() {
  bRows.value.push({
    category: '',
    subcategory: '',
    level1_indicator: '',
    level2_indicator: '',
    weight: 2,
  })
}

function removeBRow(index: number) {
  bRows.value.splice(index, 1)
}

async function saveA() {
  if (selectedJobId.value === null) return
  saving.value = true
  try {
    aRows.value = await saveStandardA(selectedJobId.value, aRows.value)
    ElMessage.success('A 表已保存')
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : '保存失败')
  } finally {
    saving.value = false
  }
}

async function saveB() {
  if (selectedJobId.value === null) return
  saving.value = true
  try {
    bRows.value = await saveStandardB(selectedJobId.value, bRows.value)
    ElMessage.success('B 表已保存')
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : '保存失败')
  } finally {
    saving.value = false
  }
}

function onLogout() {
  clearToken()
  router.push({ name: 'login' })
}

onMounted(async () => {
  try {
    await listJobs().then((list) => (jobs.value = list))
    const preset = route.query.job ? Number(route.query.job) : null
    const target = jobs.value.find((j) => j.id === preset) ?? jobs.value[0]
    if (target) {
      selectedJobId.value = target.id
      await loadStandard()
    }
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : '加载失败')
  }
})
</script>

<template>
  <div class="scoring">
    <header class="bar">
      <h1>评分标准配置</h1>
      <div class="actions">
        <el-button @click="router.push({ name: 'home' })">首页</el-button>
        <el-button @click="onLogout">退出登录</el-button>
      </div>
    </header>

    <el-card>
      <div class="toolbar">
        <span class="label">招聘岗位：</span>
        <el-select
          v-model="selectedJobId"
          placeholder="请选择岗位"
          style="width: 280px"
          @change="onJobChange"
        >
          <el-option
            v-for="j in jobs"
            :key="j.id"
            :label="`${j.name}（${j.code}）`"
            :value="j.id"
          />
        </el-select>
      </div>

      <el-tabs v-model="activeTab">
        <el-tab-pane label="A 表（分数分配）" name="a">
          <div class="panel">
            <div class="row-actions">
              <el-button size="small" @click="addARow">添加行</el-button>
              <span class="hint">
                大类分数合计：
                <b :class="{ ok: Math.abs(categoryTotal - 10) < 0.01 }">{{ categoryTotal }}</b>
                / 10
              </span>
              <el-button type="primary" size="small" :loading="saving" @click="saveA">
                保存 A 表
              </el-button>
            </div>
            <el-table v-loading="loading" :data="aRows" border>
              <el-table-column label="大类" min-width="130">
                <template #default="{ row }">
                  <el-input v-model="row.category" size="small" />
                </template>
              </el-table-column>
              <el-table-column label="小类" min-width="130">
                <template #default="{ row }">
                  <el-input v-model="row.subcategory" size="small" />
                </template>
              </el-table-column>
              <el-table-column label="大类分数" width="150">
                <template #default="{ row }">
                  <el-input-number
                    v-model="row.category_score"
                    :min="0"
                    :max="10"
                    :step="0.5"
                    size="small"
                    controls-position="right"
                  />
                </template>
              </el-table-column>
              <el-table-column label="小类分数" width="150">
                <template #default="{ row }">
                  <el-input-number
                    v-model="row.subcategory_score"
                    :min="0"
                    :max="10"
                    :step="0.5"
                    size="small"
                    controls-position="right"
                  />
                </template>
              </el-table-column>
              <el-table-column label="操作" width="80">
                <template #default="{ $index }">
                  <el-button size="small" type="danger" link @click="removeARow($index)">
                    删除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>

        <el-tab-pane label="B 表（匹配指标）" name="b">
          <div class="panel">
            <div class="row-actions">
              <el-button size="small" @click="addBRow">添加行</el-button>
              <span class="hint">权重范围 2~10</span>
              <el-button type="primary" size="small" :loading="saving" @click="saveB">
                保存 B 表
              </el-button>
            </div>
            <el-table v-loading="loading" :data="bRows" border>
              <el-table-column label="大类" min-width="120">
                <template #default="{ row }">
                  <el-input v-model="row.category" size="small" />
                </template>
              </el-table-column>
              <el-table-column label="小类" min-width="120">
                <template #default="{ row }">
                  <el-input v-model="row.subcategory" size="small" />
                </template>
              </el-table-column>
              <el-table-column label="一级指标" min-width="140">
                <template #default="{ row }">
                  <el-input v-model="row.level1_indicator" size="small" />
                </template>
              </el-table-column>
              <el-table-column label="二级指标" min-width="160">
                <template #default="{ row }">
                  <el-input v-model="row.level2_indicator" size="small" />
                </template>
              </el-table-column>
              <el-table-column label="权重" width="130">
                <template #default="{ row }">
                  <el-input-number
                    v-model="row.weight"
                    :min="2"
                    :max="10"
                    size="small"
                    controls-position="right"
                  />
                </template>
              </el-table-column>
              <el-table-column label="操作" width="80">
                <template #default="{ $index }">
                  <el-button size="small" type="danger" link @click="removeBRow($index)">
                    删除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<style scoped>
.scoring {
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

.panel {
  padding-top: 8px;
}

.row-actions {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 12px;
}

.row-actions .hint {
  color: #606266;
  font-size: 14px;
}

.row-actions .hint .ok {
  color: #67c23a;
}
</style>
