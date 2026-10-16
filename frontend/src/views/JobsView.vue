<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { clearToken } from '../api/auth'
import { createJob, listJobs, updateJob, type Job } from '../api/jobs'

const router = useRouter()
const jobs = ref<Job[]>([])
const loading = ref(false)

const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const form = reactive({ code: '', name: '', location: '' })

async function loadJobs() {
  loading.value = true
  try {
    jobs.value = await listJobs()
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : '加载失败')
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingId.value = null
  form.code = ''
  form.name = ''
  form.location = ''
  dialogVisible.value = true
}

function openEdit(job: Job) {
  editingId.value = job.id
  form.code = job.code
  form.name = job.name
  form.location = job.location
  dialogVisible.value = true
}

async function onSubmit() {
  if (!form.code || !form.name) {
    ElMessage.warning('请填写岗位代码和名称')
    return
  }
  try {
    if (editingId.value === null) {
      await createJob({ code: form.code, name: form.name, location: form.location })
      ElMessage.success('创建成功')
    } else {
      await updateJob(editingId.value, { name: form.name, location: form.location })
      ElMessage.success('保存成功')
    }
    dialogVisible.value = false
    await loadJobs()
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : '保存失败')
  }
}

async function onToggle(job: Job) {
  try {
    await updateJob(job.id, { is_active: !job.is_active })
    await loadJobs()
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : '操作失败')
  }
}

function onLogout() {
  clearToken()
  router.push({ name: 'login' })
}

onMounted(loadJobs)
</script>

<template>
  <div class="jobs">
    <header class="bar">
      <h1>招聘岗位管理</h1>
      <div class="actions">
        <el-button @click="router.push({ name: 'home' })">首页</el-button>
        <el-button @click="onLogout">退出登录</el-button>
      </div>
    </header>

    <el-card>
      <div class="toolbar">
        <el-button type="primary" @click="openCreate">新建岗位</el-button>
      </div>

      <el-table v-loading="loading" :data="jobs">
        <el-table-column prop="code" label="岗位代码" width="160" />
        <el-table-column prop="name" label="岗位名称" />
        <el-table-column prop="location" label="工作地点" width="160" />
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">
              {{ row.is_active ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button size="small" @click="openEdit(row)">编辑</el-button>
            <el-button
              size="small"
              :type="row.is_active ? 'warning' : 'success'"
              @click="onToggle(row)"
            >
              {{ row.is_active ? '停用' : '启用' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog
      v-model="dialogVisible"
      :title="editingId === null ? '新建岗位' : '编辑岗位'"
      width="480px"
    >
      <el-form label-width="90px">
        <el-form-item label="岗位代码">
          <el-input v-model="form.code" :disabled="editingId !== null" />
        </el-form-item>
        <el-form-item label="岗位名称">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="工作地点">
          <el-input v-model="form.location" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="onSubmit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.jobs {
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
</style>
