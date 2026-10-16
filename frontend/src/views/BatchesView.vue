<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type UploadFile } from 'element-plus'
import { clearToken } from '../api/auth'
import { listJobs, type Job } from '../api/jobs'
import {
  getBatch,
  listBatches,
  uploadBatch,
  type Batch,
  type Resume,
} from '../api/batches'

const router = useRouter()

const jobs = ref<Job[]>([])
const selectedJobId = ref<number | null>(null)
const selectedFile = ref<File | null>(null)
const fileName = ref('')
const batches = ref<Batch[]>([])
const loading = ref(false)
const uploading = ref(false)

const dialogVisible = ref(false)
const resumes = ref<Resume[]>([])

let timer: number | undefined

const statusMap: Record<string, { label: string; type: string }> = {
  pending: { label: '待处理', type: 'info' },
  processing: { label: '处理中', type: 'warning' },
  done: { label: '已完成', type: 'success' },
  failed: { label: '失败', type: 'danger' },
}

function jobName(id: number) {
  return jobs.value.find((j) => j.id === id)?.name ?? `岗位 #${id}`
}

async function loadJobs() {
  jobs.value = await listJobs()
  if (jobs.value.length && selectedJobId.value === null) {
    selectedJobId.value = jobs.value[0].id
  }
}

async function loadBatches() {
  loading.value = true
  try {
    batches.value = await listBatches()
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : '加载失败')
  } finally {
    loading.value = false
  }
}

function onFileChange(uploadFile: UploadFile) {
  selectedFile.value = uploadFile.raw ?? null
  fileName.value = uploadFile.name
}

async function onUpload() {
  if (selectedJobId.value === null) {
    ElMessage.warning('请选择招聘岗位')
    return
  }
  if (!selectedFile.value) {
    ElMessage.warning('请选择 ZIP 文件')
    return
  }
  uploading.value = true
  try {
    await uploadBatch(selectedJobId.value, selectedFile.value)
    ElMessage.success('上传成功，正在后台处理')
    selectedFile.value = null
    fileName.value = ''
    await loadBatches()
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : '上传失败')
  } finally {
    uploading.value = false
  }
}

async function openDetail(batch: Batch) {
  try {
    const detail = await getBatch(batch.id)
    resumes.value = detail.resumes
    dialogVisible.value = true
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : '加载失败')
  }
}

function onLogout() {
  clearToken()
  router.push({ name: 'login' })
}

onMounted(async () => {
  try {
    await loadJobs()
    await loadBatches()
    timer = window.setInterval(loadBatches, 3000)
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : '加载失败')
  }
})

onUnmounted(() => {
  if (timer) window.clearInterval(timer)
})
</script>

<template>
  <div class="batches">
    <header class="bar">
      <h1>简历上传</h1>
      <div class="actions">
        <el-button @click="router.push({ name: 'home' })">首页</el-button>
        <el-button @click="onLogout">退出登录</el-button>
      </div>
    </header>

    <el-card>
      <div class="upload-row">
        <el-select v-model="selectedJobId" placeholder="选择岗位" style="width: 260px">
          <el-option
            v-for="j in jobs"
            :key="j.id"
            :label="`${j.name}（${j.code}）`"
            :value="j.id"
          />
        </el-select>
        <el-upload
          :auto-upload="false"
          :limit="1"
          accept=".zip"
          :show-file-list="false"
          :on-change="onFileChange"
        >
          <el-button>选择 ZIP 文件</el-button>
        </el-upload>
        <span v-if="fileName" class="file-name">{{ fileName }}</span>
        <el-button type="primary" :loading="uploading" @click="onUpload">上传</el-button>
      </div>

      <el-table v-loading="loading" :data="batches">
        <el-table-column prop="id" label="批次" width="80" />
        <el-table-column label="岗位" width="180">
          <template #default="{ row }">{{ jobName(row.job_id) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="statusMap[row.status]?.type ?? 'info'">
              {{ statusMap[row.status]?.label ?? row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="进度" width="140">
          <template #default="{ row }">
            {{ row.processed_count }} / {{ row.total_count }}
          </template>
        </el-table-column>
        <el-table-column prop="error" label="错误" show-overflow-tooltip />
        <el-table-column prop="created_at" label="上传时间" width="180" />
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button size="small" @click="openDetail(row)">查看简历</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" title="简历列表" width="720px">
      <el-table :data="resumes">
        <el-table-column prop="original_filename" label="文件名" />
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="row.status === 'parsed' ? 'success' : 'danger'">
              {{ row.status === 'parsed' ? '已解析' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="error" label="错误" show-overflow-tooltip />
      </el-table>
    </el-dialog>
  </div>
</template>

<style scoped>
.batches {
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

.upload-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.file-name {
  color: #606266;
  font-size: 14px;
}
</style>
