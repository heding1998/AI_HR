<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { listJobs } from '../api/jobs'
import { listBatches } from '../api/batches'
import { listApplications } from '../api/applications'
import { listTalentPool } from '../api/talentPool'

const counts = ref({
  jobs: 0,
  batches: 0,
  applications: 0,
  talent: 0,
})

const stats = [
  { key: 'jobs', label: '招聘岗位', route: 'jobs' },
  { key: 'batches', label: '简历批次', route: 'batches' },
  { key: 'applications', label: '应聘记录', route: 'applications' },
  { key: 'talent', label: '高分人才', route: 'talent-pool' },
] as const

onMounted(async () => {
  const [jobs, batches, applications, talent] = await Promise.allSettled([
    listJobs(),
    listBatches(),
    listApplications(),
    listTalentPool(),
  ])
  counts.value.jobs = jobs.status === 'fulfilled' ? jobs.value.length : 0
  counts.value.batches = batches.status === 'fulfilled' ? batches.value.length : 0
  counts.value.applications = applications.status === 'fulfilled' ? applications.value.length : 0
  counts.value.talent = talent.status === 'fulfilled' ? talent.value.length : 0
})
</script>

<template>
  <div class="home">
    <section class="hero">
      <h2 class="hero-title">简历初筛工作台</h2>
      <p class="hero-sub">上传简历 ZIP → 解析 → AI 评分 → 高分人才库，一站式完成初筛。</p>
    </section>

    <section class="grid">
      <router-link
        v-for="s in stats"
        :key="s.key"
        :to="{ name: s.route }"
        class="stat-card"
      >
        <span class="stat-label">{{ s.label }}</span>
        <span class="stat-value num">{{ counts[s.key] }}</span>
        <span class="stat-link">查看 →</span>
      </router-link>
    </section>
  </div>
</template>

<style scoped>
.home {
  max-width: 960px;
}

.hero {
  margin-bottom: 24px;
}

.hero-title {
  font-size: 22px;
  font-weight: 600;
}

.hero-sub {
  margin-top: 8px;
  color: var(--ink-3);
  font-size: 14px;
}

.grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.stat-card {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.stat-card:hover {
  border-color: var(--teal);
  box-shadow: 0 6px 18px rgba(27, 34, 51, 0.06);
}

.stat-label {
  font-size: 13px;
  color: var(--ink-3);
}

.stat-value {
  font-size: 32px;
  font-weight: 600;
  color: var(--ink);
}

.stat-link {
  font-size: 13px;
  color: var(--teal);
}

@media (max-width: 900px) {
  .grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
