import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import Dashboard from '../views/Dashboard.vue'
import UserProfile from '../views/UserProfile.vue'
import Datasets from '../views/Datasets.vue'
import ModelTraining from '../views/ModelTraining.vue'
import ModelTesting from '../views/ModelTesting.vue'
import ModelFeedback from '../views/ModelFeedback.vue'
import ModelUpload from '../views/ModelUpload.vue'
import Segmentation from '../views/Segmentation.vue'
import History from '../views/History.vue'
import Guide from '../views/Guide.vue'
import Admin from '../views/Admin.vue'

// 路由守卫 - 检查登录状态
const requireAuth = (to, from, next) => {
  const user = localStorage.getItem('user')
  if (!user) {
    next('/login')
  } else {
    next()
  }
}

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', component: Login },
  { path: '/register', component: Register },
  {
    path: '/dashboard',
    component: Dashboard,
    beforeEnter: requireAuth,
    children: [
      { path: '', redirect: '/segmentation' },
      { path: '/user/profile', component: UserProfile, beforeEnter: requireAuth },
      { path: '/datasets', component: Datasets, beforeEnter: requireAuth },
      { path: '/model/training', component: ModelTraining, beforeEnter: requireAuth },
      { path: '/model/testing', component: ModelTesting, beforeEnter: requireAuth },
      { path: '/model/upload', component: ModelUpload, beforeEnter: requireAuth },
      { path: '/model/feedback', component: ModelFeedback, beforeEnter: requireAuth },
      { path: '/segmentation', component: Segmentation, beforeEnter: requireAuth },
      { path: '/history', component: History, beforeEnter: requireAuth },
      { path: '/guide', component: Guide, beforeEnter: requireAuth },
      { path: '/admin', component: Admin, beforeEnter: requireAuth }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
