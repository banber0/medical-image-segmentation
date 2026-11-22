<template>
  <el-container class="dashboard-container">
    <!-- 左侧侧边栏 -->
    <el-aside width="220px" class="sidebar">
      <div class="logo">
        <el-icon :size="32" color="#409eff"><FirstAidKit /></el-icon>
        <h3>医学影像分割</h3>
      </div>

      <el-menu
        :default-active="activeMenu"
        class="el-menu-vertical"
        router
      >
        <el-menu-item index="/user/profile">
          <el-icon><User /></el-icon>
          <span>个人信息</span>
        </el-menu-item>
        <el-menu-item index="/datasets">
          <el-icon><FolderOpened /></el-icon>
          <span>数据集</span>
        </el-menu-item>
        <el-menu-item index="/model/training">
          <el-icon><Cpu /></el-icon>
          <span>模型训练</span>
        </el-menu-item>
        <el-menu-item index="/model/upload">
          <el-icon><Upload /></el-icon>
          <span>上传模型</span>
        </el-menu-item>
        <el-menu-item index="/model/testing">
          <el-icon><Aim /></el-icon>
          <span>模型评估</span>
        </el-menu-item>
        <el-menu-item index="/model/feedback">
          <el-icon><ChatDotRound /></el-icon>
          <span>模型反馈</span>
        </el-menu-item>
        <el-menu-item index="/segmentation">
          <el-icon><Operation /></el-icon>
          <span>影像分割</span>
        </el-menu-item>
        <el-menu-item index="/history">
          <el-icon><Clock /></el-icon>
          <span>历史记录</span>
        </el-menu-item>
        <el-menu-item index="/guide" v-if="userType !== 'admin'">
          <el-icon><Reading /></el-icon>
          <span>使用指南</span>
        </el-menu-item>
        <el-menu-item index="/admin" v-if="userType === 'admin'">
          <el-icon><Setting /></el-icon>
          <span>管理员面板</span>
        </el-menu-item>

        <div style="flex-grow: 1;"></div>

        <el-menu-item index="10" @click="logout">
          <el-icon><SwitchButton /></el-icon>
          <span>退出登录</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 右侧主内容区 -->
    <el-main class="main-content">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  FirstAidKit, User, FolderOpened, Cpu, Aim,
  ChatDotRound, Operation, Clock, Reading, Setting, SwitchButton, Upload
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()

const activeMenu = computed(() => route.path)

const userInfo = computed(() => {
  const user = localStorage.getItem('user')
  return user ? JSON.parse(user) : null
})

const userType = computed(() => userInfo.value?.user_type || 'user')

onMounted(() => {
  if (!localStorage.getItem('user')) {
    router.push('/login')
  }
})

const logout = () => {
  localStorage.removeItem('user')
  ElMessage.success('已退出登录')
  router.push('/login')
}
</script>

<style scoped>
.dashboard-container {
  height: 100vh;
  background-color: #f5f7fa;
}

.sidebar {
  background-color: #fff;
  box-shadow: 2px 0 8px rgba(0,0,0,0.05);
  display: flex;
  flex-direction: column;
}

.logo {
  padding: 20px 15px;
  display: flex;
  align-items: center;
  gap: 10px;
  border-bottom: 1px solid #f0f0f0;
}

.logo h3 {
  margin: 0;
  font-size: 16px;
  color: #303133;
  white-space: nowrap;
}

.el-menu-vertical {
  border-right: none;
  flex-grow: 1;
  display: flex;
  flex-direction: column;
}

.el-menu-item {
  height: 50px;
  line-height: 50px;
}

.main-content {
  padding: 0;
  background-color: #f5f7fa;
}
</style>
