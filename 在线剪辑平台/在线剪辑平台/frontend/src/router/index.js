import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/HomePage.vue')
  },
  {
    path: '/upload',
    name: 'Upload',
    component: () => import('@/views/UploadPage.vue')
  },
  {
    path: '/editor',
    name: 'Editor',
    component: () => import('@/views/EditorPage.vue')
  },
  {
    path: '/progress',
    name: 'Progress',
    component: () => import('@/views/ProgressPage.vue')
  },
  {
    path: '/download',
    name: 'Download',
    component: () => import('@/views/DownloadPage.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
