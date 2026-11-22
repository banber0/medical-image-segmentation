<template>
  <el-container class="dashboard-container">
    <!-- 左侧侧边栏 -->
    <el-aside width="200px" class="sidebar">
      <div class="logo">
        <h3>智能医学影像分割平台</h3>
      </div>
      <el-menu default-active="9" class="el-menu-vertical">
        <el-menu-item index="1" @click="$router.push('/user/profile')">个人信息</el-menu-item>
        <el-menu-item index="2" @click="$router.push('/datasets')">数据集</el-menu-item>
        <el-menu-item index="3" @click="$router.push('/model/training')">模型训练</el-menu-item>
        <el-menu-item index="4" @click="$router.push('/model/testing')">测试模型</el-menu-item>
        <el-menu-item index="5" @click="$router.push('/model/feedback')">模型反馈</el-menu-item>
        <el-menu-item index="6" @click="$router.push('/segmentation')">影像分割</el-menu-item>
        <el-menu-item index="7" @click="$router.push('/history')">历史记录</el-menu-item>
        <el-menu-item index="8" @click="$router.push('/guide')">指南</el-menu-item>
        <el-menu-item index="9" @click="$router.push('/background')" style="color: #409EFF; font-weight: bold;">背景</el-menu-item>
        <div style="flex-grow: 1;"></div> <!-- 占位推到底部 -->
        <el-menu-item index="10" @click="logout" style="margin-top: 50px;">退出登录</el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 右侧主内容区 -->
    <el-main class="main-content">
      <h2>系统背景</h2>
      <el-card class="background-card">
        <div class="background-content">
          <h3>项目背景</h3>
          <p>医学影像是现代医学诊断的重要工具，其中影像分割是医学影像处理的关键步骤。准确的医学影像分割可以帮助医生更好地理解病变区域，提高诊断准确性和治疗效果。</p>
          <p>传统的医学影像分割方法往往需要大量的人工干预，效率低下且准确性有限。随着深度学习技术的发展，基于卷积神经网络的分割方法取得了显著的成果，其中Unet模型因其在医学影像分割任务中的出色表现而被广泛应用。</p>
          <p>本项目基于ResNet34-UNet实现二维灰度医学影像的二值分割，提供数据集管理、模型训练、分割与评估功能，用于课程学习和算法演示。</p>

          <h3>技术栈</h3>
          <div class="tech-stack">
            <el-row :gutter="20">
              <el-col :span="8">
                <el-card class="tech-card">
                  <h4>前端</h4>
                  <ul>
                    <li>Vue 3</li>
                    <li>JavaScript</li>
                    <li>Element Plus</li>
                    <li>Vue Router</li>
                  </ul>
                </el-card>
              </el-col>
              <el-col :span="8">
                <el-card class="tech-card">
                  <h4>后端</h4>
                  <ul>
                    <li>Flask</li>
                    <li>Flask-SQLAlchemy</li>
                    <li>MySQL</li>
                  </ul>
                </el-card>
              </el-col>
              <el-col :span="8">
                <el-card class="tech-card">
                  <h4>算法端</h4>
                  <ul>
                    <li>segmentation-models-pytorch</li>
                    <li>PyTorch</li>
                    <li>ResNet34-UNet</li>
                  </ul>
                </el-card>
              </el-col>
            </el-row>
          </div>

          <h3>系统架构</h3>
          <p>系统采用前后端分离的架构设计，主要分为三个部分：</p>
          <ol>
            <li><strong>前端</strong>：使用Vue 3 + JavaScript + Element Plus构建，负责用户界面和交互。</li>
            <li><strong>后端</strong>：使用Flask + Flask-SQLAlchemy + MySQL构建，负责数据管理和业务逻辑。</li>
            <li><strong>算法端</strong>：使用PyTorch + segmentation-models-pytorch构建，由Flask调用训练和推理模块。</li>
          </ol>

          <h3>核心功能</h3>
          <ul>
            <li><strong>用户管理</strong>：注册、登录、个人信息管理。</li>
            <li><strong>数据集管理</strong>：上传、查看、编辑、删除数据集。</li>
            <li><strong>模型训练</strong>：选择数据集、设置训练配置、模型训练。</li>
            <li><strong>模型测试</strong>：单样例评估、评估指标计算。</li>
            <li><strong>模型反馈</strong>：收集用户对模型的反馈。</li>
            <li><strong>影像分割</strong>：使用训练好的模型进行影像分割。</li>
            <li><strong>历史记录</strong>：管理分割、训练、评估历史。</li>
            <li><strong>管理员功能</strong>：系统管理、用户管理。</li>
          </ul>

          <h3>应用场景</h3>
          <p>本系统可应用于以下场景：</p>
          <ul>
            <li>医学影像分割算法演示</li>
            <li>医学研究</li>
            <li>医学教育</li>
            <li>医学影像分析</li>
          </ul>
        </div>
      </el-card>
    </el-main>
  </el-container>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

const router = useRouter()

const logout = () => {
  localStorage.removeItem('user')
  ElMessage.success('已退出登录')
  router.push('/login')
}
</script>

<style scoped>
/* 全局布局 */
.dashboard-container {
  height: 100vh;
  background-color: #fafafa;
}

/* 侧边栏样式 */
.sidebar {
  background-color: #fff;
  box-shadow: 2px 0 8px rgba(0,0,0,0.05);
  display: flex;
  flex-direction: column;
}
.logo {
  padding: 20px 10px;
  text-align: center;
  border-bottom: 1px solid #f0f0f0;
}
.el-menu-vertical {
  border-right: none;
  flex-grow: 1;
  display: flex;
  flex-direction: column;
}

/* 主内容区 */
.main-content {
  padding: 30px;
}

.background-card {
  margin-top: 20px;
}

.background-content {
  padding: 20px;
  line-height: 1.6;
}

.background-content h3 {
  margin-top: 30px;
  margin-bottom: 15px;
  color: #303133;
}

.tech-stack {
  margin-top: 20px;
  margin-bottom: 30px;
}

.tech-card {
  height: 150px;
}

.tech-card h4 {
  margin-bottom: 15px;
  text-align: center;
}

.tech-card ul {
  margin-left: 20px;
}

.tech-card li {
  margin-bottom: 5px;
}
</style>
