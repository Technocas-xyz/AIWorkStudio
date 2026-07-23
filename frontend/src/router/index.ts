import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/pages/LoginPage.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/',
    component: () => import('@/layouts/AppLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      { path: '', redirect: '/dashboard' },
      { path: 'dashboard', name: 'Dashboard', component: () => import('@/pages/DashboardPage.vue') },
      { path: 'projects', name: 'Projects', component: () => import('@/pages/ProjectsPage.vue') },
      { path: 'artwork-library', name: 'ArtworkLibrary', component: () => import('@/pages/ArtworkLibraryPage.vue') },
      { path: 'analysis', name: 'Analysis', component: () => import('@/pages/AnalysisPage.vue') },
      { path: 'reconstruction', name: 'Reconstruction', component: () => import('@/pages/ReconstructionPage.vue') },
      { path: 'production-planning', name: 'ProductionPlanning', component: () => import('@/pages/ProductionPlanningPage.vue') },
      { path: 'generation', name: 'Generation', component: () => import('@/pages/GenerationPage.vue') },
      { path: 'quality', name: 'Quality', component: () => import('@/pages/QualityAssurancePage.vue') },
      { path: 'export', name: 'Export', component: () => import('@/pages/WorkspacePage.vue'), props: { workspace: 'Export Center' } },
      { path: 'administration', name: 'Administration', component: () => import('@/pages/WorkspacePage.vue'), props: { workspace: 'Administration' } },
      { path: 'settings', name: 'Settings', component: () => import('@/pages/WorkspacePage.vue'), props: { workspace: 'Settings' } },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/pages/NotFoundPage.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  const authStore = useAuthStore()

  // Wait for initialization
  if (!authStore.isInitialized) {
    await authStore.initialize()
  }

  if (to.meta.requiresAuth !== false && !authStore.isAuthenticated) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }

  if (to.path === '/login' && authStore.isAuthenticated) {
    return { path: '/dashboard' }
  }
})

export default router
