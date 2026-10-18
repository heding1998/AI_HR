import { createRouter, createWebHistory } from 'vue-router'
import { getToken } from '../api/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
    },
    {
      path: '/',
      component: () => import('../layouts/AppLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'home',
          component: () => import('../views/HomeView.vue'),
          meta: { title: '首页' },
        },
        {
          path: 'jobs',
          name: 'jobs',
          component: () => import('../views/JobsView.vue'),
          meta: { title: '招聘岗位管理' },
        },
        {
          path: 'scoring-standard',
          name: 'scoring-standard',
          component: () => import('../views/ScoringStandardView.vue'),
          meta: { title: '评分标准配置' },
        },
        {
          path: 'batches',
          name: 'batches',
          component: () => import('../views/BatchesView.vue'),
          meta: { title: '简历上传' },
        },
        {
          path: 'applications',
          name: 'applications',
          component: () => import('../views/ApplicationsView.vue'),
          meta: { title: '评分结果' },
        },
        {
          path: 'talent-pool',
          name: 'talent-pool',
          component: () => import('../views/TalentPoolView.vue'),
          meta: { title: '高分人才库' },
        },
      ],
    },
  ],
})

router.beforeEach((to) => {
  const authed = getToken() !== null
  if (to.meta.requiresAuth && !authed) {
    return { name: 'login' }
  }
  if (to.name === 'login' && authed) {
    return { name: 'home' }
  }
})

export default router
