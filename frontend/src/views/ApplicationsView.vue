<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { listJobs, type Job } from '../api/jobs'
import { listApplications, type Application } from '../api/applications'

const jobs = ref<Job[]>([])
const applications = ref<Application[]>([])
const selectedJobId = ref<number>(0) // 0 = 全部岗位
const loading = ref(false)

const statusMap: Record<string, { label: string; type: string }> = {
  passed: { label: '初筛通过', type: 'success' },
  failed: { label: '初筛不通过', type: 'danger' },
}

function jobName(id: number) {
  return jobs.value.find((j) => j.id === id)?.name ?? `岗位 #${id}`
}

async function loadApplications() {
  loading.value = true
  try {
    applications.value = await listApplications(
      selectedJobId.value === 0 ? undefined : selectedJobId.value,
    )
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : '加载失败')
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  try {
    jobs.value = await listJobs()
    await loadApplications()
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : '加载失败')
  }
})
</script>

<template>
  <div class="applications">
    <el-card>
      <div class="toolbar">
        <span class="label">招聘岗位：</span>
        <el-select v-model="selectedJobId" style="width: 280px" @change="loadApplications">
          <el-option label="全部岗位" :value="0" />
          <el-option
            v-for="j in jobs"
            :key="j.id"
            :label="`${j.name}（${j.code}）`"
            :value="j.id"
          />
        </el-select>
      </div>

      <el-table v-loading="loading" :data="applications">
        <el-table-column prop="candidate_name" label="姓名" width="120" />
        <el-table-column prop="candidate_contact" label="联系方式" width="160" />
        <el-table-column label="岗位" min-width="160">
          <template #default="{ row }">{{ jobName(row.job_id) }}</template>
        </el-table-column>
        <el-table-column label="分数" width="100" sortable>
          <template #default="{ row }">
            <span class="score-num">{{ row.score }}</span>
          </template>
        </el-table-column>
        <el-table-column label="初筛状态" width="120">
          <template #default="{ row }">
            <el-tag :type="statusMap[row.status]?.type ?? 'info'">
              {{ statusMap[row.status]?.label ?? row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="时间" width="180" />
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
</style>
