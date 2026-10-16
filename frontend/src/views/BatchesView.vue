<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type UploadFile } from 'element-plus'
import { clearToken } from '../api/auth'
import { listJobs, type Job } from '../api/jobs'
import {
  getBatch,
  getResume,
  listBatches,
  rescoreResume,
  uploadBatch,
  type Batch,
  type Resume,
  type ResumeDetail,
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

const resumeDetailVisible = ref(false)
const resumeDetailLoading = ref(false)
const resumeDetail = ref<ResumeDetail | null>(null)
const rescoring = ref(false)

let timer: number | undefined

const statusMap: Record<string, { label: string; type: string }> = {
  pending: { label: '待处理', type: 'info' },
  processing: { label: '处理中', type: 'warning' },
  done: { label: '已完成', type: 'success' },
  failed: { label: '失败', type: 'danger' },
}

const resumeStatusMap: Record<string, { label: string; type: string }> = {
  parsed: { label: '已解析', type: 'info' },
  extracted: { label: '已提取', type: 'success' },
  failed: { label: '失败', type: 'danger' },
  anomaly: { label: '异常', type: 'warning' },
}

const FIELD_LABELS: Record<string, string> = {
  name: '姓名',
  gender: '性别',
  age: '年龄',
  highest_education: '最高学历',
  contact: '联系方式',
  work_years: '工作年限',
  job_intention: '求职意向',
  expected_salary: '期望薪资',
  expected_city: '期望城市',
  skills: '个人技能',
  work_experience: '工作经验',
  project_experience: '项目经验',
  self_evaluation: '自我评价',
}

const FIELD_ORDER = [
  'name',
  'gender',
  'age',
  'highest_education',
  'contact',
  'work_years',
  'job_intention',
  'expected_salary',
  'expected_city',
  'skills',
  'work_experience',
  'project_experience',
  'self_evaluation',
]

function jobName(id: number) {
  return jobs.value.find((j) => j.id === id)?.name ?? `岗位 #${id}`
}

function fieldValue(key: string): string {
  const content = resumeDetail.value?.extracted_content
  if (!content) return '—'
  const value = content[key]
  if (value === null || value === undefined || value === '') return '—'
  if (Array.isArray(value)) return value.map(String).join('、')
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
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

async function openResumeDetail(resume: Resume) {
  resumeDetailLoading.value = true
  try {
    resumeDetail.value = await getResume(resume.id)
    resumeDetailVisible.value = true
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : '加载失败')
  } finally {
    resumeDetailLoading.value = false
  }
}

async function onRescore(resume: ResumeDetail) {
  rescoring.value = true
  try {
    const updated = await rescoreResume(resume.id)
    resumeDetail.value = updated
    const row = resumes.value.find((r) => r.id === updated.id)
    if (row) {
      row.score = updated.score
      row.score_error = updated.score_error
    }
    ElMessage.success('评分完成')
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : '评分失败')
  } finally {
    rescoring.value = false
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

    <el-dialog v-model="dialogVisible" title="简历列表" width="760px">
      <el-table :data="resumes">
        <el-table-column prop="original_filename" label="文件名" />
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="resumeStatusMap[row.status]?.type ?? 'info'">
              {{ resumeStatusMap[row.status]?.label ?? row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="分数" width="90">
          <template #default="{ row }">
            <span v-if="row.score !== null && row.score !== undefined">{{ row.score }}</span>
            <el-tag v-else type="warning" size="small">未评分</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="error" label="错误" show-overflow-tooltip />
        <el-table-column label="操作" width="90">
          <template #default="{ row }">
            <el-button size="small" @click="openResumeDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <el-dialog
      v-model="resumeDetailVisible"
      :title="resumeDetail?.original_filename ?? '简历详情'"
      width="720px"
    >
      <div v-loading="resumeDetailLoading">
        <div v-if="resumeDetail" class="score-bar">
          <span class="score-label">评分</span>
          <span v-if="resumeDetail.score !== null" class="score-value">
            {{ resumeDetail.score }}
          </span>
          <el-tag v-else type="warning" size="small">未评分</el-tag>
          <span v-if="resumeDetail.score_error" class="score-error">
            {{ resumeDetail.score_error }}
          </span>
          <el-button
            size="small"
            type="primary"
            :loading="rescoring"
            @click="onRescore(resumeDetail)"
          >
            重新评分
          </el-button>
        </div>

        <el-descriptions v-if="resumeDetail" :column="2" border>
          <el-descriptions-item
            v-for="key in FIELD_ORDER"
            :key="key"
            :label="FIELD_LABELS[key]"
          >
            {{ fieldValue(key) }}
          </el-descriptions-item>
        </el-descriptions>

        <template v-if="resumeDetail?.extracted_text">
          <h4 class="raw-title">原文</h4>
          <pre class="raw-text">{{ resumeDetail.extracted_text }}</pre>
        </template>
      </div>
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

.raw-title {
  margin: 16px 0 8px;
}

.score-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

.score-label {
  color: #606266;
  font-size: 14px;
}

.score-value {
  font-size: 20px;
  font-weight: 600;
  color: #409eff;
}

.score-error {
  color: #f56c6c;
  font-size: 13px;
}

.raw-text {
  max-height: 300px;
  overflow: auto;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 4px;
  white-space: pre-wrap;
  font-size: 13px;
}
</style>
