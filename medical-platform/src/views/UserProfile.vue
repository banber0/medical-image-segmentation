<template>
  <div class="profile-view">
    <div class="header">
      <h2>个人中心</h2>
    </div>

    <el-row :gutter="20">
      <el-col :span="12">
        <el-card class="profile-card">
          <template #header>
            <div class="card-header">
              <span>个人信息</span>
            </div>
          </template>

          <el-form :model="userInfo" label-width="100px">
            <el-form-item label="用户名">
              <el-input v-model="userInfo.username" disabled></el-input>
            </el-form-item>
            <el-form-item label="邮箱">
              <el-input v-model="userInfo.email" placeholder="请输入邮箱"></el-input>
            </el-form-item>
            <el-form-item label="手机号">
              <el-input v-model="userInfo.phone" placeholder="请输入手机号"></el-input>
            </el-form-item>
            <el-form-item label="所属机构">
              <el-input v-model="userInfo.organization" placeholder="请输入所属机构"></el-input>
            </el-form-item>
            <el-form-item label="用户类型">
              <el-select v-model="userInfo.userType" disabled style="width: 100%;">
                <el-option label="普通用户" value="user"></el-option>
                <el-option label="管理员" value="admin"></el-option>
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveProfile">
                <el-icon><Check /></el-icon>
                保存修改
              </el-button>
              <el-button @click="resetForm">重置</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card class="password-card">
          <template #header>
            <div class="card-header">
              <span>修改密码</span>
            </div>
          </template>

          <el-form :model="passwordForm" label-width="100px">
            <el-form-item label="当前密码">
              <el-input v-model="passwordForm.oldPassword" type="password" show-password placeholder="请输入当前密码"></el-input>
            </el-form-item>
            <el-form-item label="新密码">
              <el-input v-model="passwordForm.newPassword" type="password" show-password placeholder="请输入新密码"></el-input>
            </el-form-item>
            <el-form-item label="确认密码">
              <el-input v-model="passwordForm.confirmPassword" type="password" show-password placeholder="请再次输入新密码"></el-input>
            </el-form-item>
            <el-form-item>
              <el-button type="danger" @click="changePassword">
                <el-icon><Lock /></el-icon>
                修改密码
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>

    <!-- 用户统计信息 -->
    <el-card class="stats-card" style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>我的数据统计</span>
        </div>
      </template>

      <el-row :gutter="20">
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-icon" style="background-color: #409eff;">
              <el-icon :size="30"><Folder /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.datasetCount }}</div>
              <div class="stat-label">数据集</div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-icon" style="background-color: #67c23a;">
              <el-icon :size="30"><Cpu /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.modelCount }}</div>
              <div class="stat-label">模型</div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-icon" style="background-color: #e6a23c;">
              <el-icon :size="30"><Operation /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.segmentCount }}</div>
              <div class="stat-label">分割次数</div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-icon" style="background-color: #f56c6c;">
              <el-icon :size="30"><Clock /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.evalCount }}</div>
              <div class="stat-label">评估次数</div>
            </div>
          </div>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Check, Lock, Folder, Cpu, Operation, Clock } from '@element-plus/icons-vue'
import { userAPI, datasetAPI, modelAPI, segmentationAPI, evaluateAPI } from '../api/index'

const userInfo = reactive({
  username: '',
  email: '',
  phone: '',
  organization: '',
  userType: 'user'
})

const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const stats = reactive({
  datasetCount: 0,
  modelCount: 0,
  segmentCount: 0,
  evalCount: 0
})

const currentUser = computed(() => {
  const user = localStorage.getItem('user')
  return user ? JSON.parse(user) : null
})

const fetchUserProfile = async () => {
  try {
    const res = await userAPI.getProfile(currentUser.value?.username)
    if (res.success && res.user) {
      userInfo.username = res.user.username || currentUser.value?.username
      userInfo.email = res.user.email || ''
      userInfo.phone = res.user.phone || ''
      userInfo.organization = res.user.organization || ''
      userInfo.userType = res.user.userType || 'user'
    }
  } catch (error) {
    console.error('获取用户信息失败', error)
  }
}

const fetchStats = async () => {
  try {
    const userId = currentUser.value?.user_id

    const [dsRes, modelRes, segRes, evalRes] = await Promise.all([
      datasetAPI.getList(userId),
      modelAPI.getList(userId),
      segmentationAPI.getHistory(userId),
      evaluateAPI.getHistory(userId)
    ])

    if (dsRes.success) stats.datasetCount = dsRes.datasets?.length || 0
    if (modelRes.success) stats.modelCount = modelRes.models?.length || 0
    if (segRes.success) stats.segmentCount = segRes.history?.length || 0
    if (evalRes.success) stats.evalCount = evalRes.history?.length || 0
  } catch (error) {
    console.error('获取统计数据失败', error)
  }
}

const saveProfile = async () => {
  try {
    const res = await userAPI.updateProfile({
      username: userInfo.username,
      email: userInfo.email,
      phone: userInfo.phone,
      organization: userInfo.organization
    })

    if (res.success) {
      ElMessage.success('保存成功')
    }
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

const changePassword = async () => {
  if (!passwordForm.oldPassword || !passwordForm.newPassword) {
    ElMessage.warning('请填写完整信息')
    return
  }

  if (passwordForm.newPassword !== passwordForm.confirmPassword) {
    ElMessage.error('两次输入的密码不一致')
    return
  }

  if (passwordForm.newPassword.length < 6) {
    ElMessage.error('密码长度至少6位')
    return
  }

  // 从 currentUser 获取 username
  const username = currentUser.value?.username
  if (!username) {
    ElMessage.error('用户未登录')
    return
  }

  try {
    const res = await userAPI.changePassword(username, {
      oldPassword: passwordForm.oldPassword,
      newPassword: passwordForm.newPassword
    })

    if (res.success) {
      ElMessage.success('密码修改成功')
      passwordForm.oldPassword = ''
      passwordForm.newPassword = ''
      passwordForm.confirmPassword = ''
    }
  } catch (error) {
    ElMessage.error(error.message || '密码修改失败')
  }
}

const resetForm = () => {
  fetchUserProfile()
}

onMounted(() => {
  userInfo.username = currentUser.value?.username || ''
  fetchUserProfile()
  fetchStats()
})
</script>

<style scoped>
.profile-view {
  padding: 20px;
}

.header {
  margin-bottom: 20px;
}

.header h2 {
  margin: 0;
  font-size: 20px;
  color: #303133;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stats-card {
  margin-top: 20px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 20px;
  background-color: #f5f7fa;
  border-radius: 8px;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  color: #fff;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}
</style>
