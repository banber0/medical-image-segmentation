<template>
  <div class="guide-view">
    <div class="header">
      <h2>系统使用指南</h2>
    </div>

    <el-card class="guide-card">
      <el-collapse v-model="activeNames">
        <el-collapse-item title="1. 系统介绍" name="1">
          <div class="guide-content">
            <p>医学影像分割系统是一个基于Unet深度学习模型的医学影像分割平台，支持肝脏和病理细胞的分割任务。</p>
            <p>系统主要功能包括：</p>
            <ul>
              <li>用户注册登录</li>
              <li>数据集管理（上传、编辑、删除）</li>
              <li>模型训练（选择数据集、设置训练配置）</li>
              <li>模型评估（单样例评估、评估指标展示）</li>
              <li>模型反馈</li>
              <li>影像分割（实时分割、结果展示）</li>
              <li>历史记录管理</li>
            </ul>
          </div>
        </el-collapse-item>

        <el-collapse-item title="2. 快速开始" name="2">
          <div class="guide-content">
            <h4>2.1 注册登录</h4>
            <p>1. 在登录页面点击"立即注册"，填写用户名和密码进行注册。</p>
            <p>2. 注册成功后，使用账号和密码登录系统。</p>

            <h4>2.2 上传数据集</h4>
            <p>1. 登录后，点击左侧菜单的"数据集"。</p>
            <p>2. 点击"上传数据集"按钮，填写数据集名称、描述和类型。</p>
            <p>3. 选择数据集文件（支持zip格式），点击"上传"按钮。</p>
            <p class="tip">提示：数据集需要包含 images 和 masks 两个文件夹</p>

            <h4>2.3 模型训练</h4>
            <p>1. 点击左侧菜单的"模型训练"。</p>
            <p>2. 填写模型名称并选择要使用的数据集。</p>
            <p>3. 设置训练参数（批次大小、学习率、训练轮数等）。</p>
            <p>4. 点击"开始训练"按钮，等待训练完成。</p>

            <h4>2.4 模型评估</h4>
            <p>1. 点击左侧菜单的"模型评估"。</p>
            <p>2. 选择已训练完成的模型。</p>
            <p>3. 上传待评估图片和对应的标签图片。</p>
            <p>4. 点击"开始评估"按钮，查看评估指标和结果对比。</p>

            <h4>2.5 影像分割</h4>
            <p>1. 点击左侧菜单的"影像分割"。</p>
            <p>2. 选择已训练完成的模型。</p>
            <p>3. 上传待分割的医学影像。</p>
            <p>4. 点击"开始分割"按钮，查看分割结果。</p>
          </div>
        </el-collapse-item>

        <el-collapse-item title="3. 数据集格式要求" name="3">
          <div class="guide-content">
            <p>上传的数据集需要按照以下格式组织：</p>
            <pre class="code-block">
dataset.zip
├── images/          # 原始医学影像
│   ├── image1.png
│   ├── image2.png
│   └── ...
└── masks/           # 分割标签掩膜
    ├── image1.png
    ├── image2.png
    └── ...
            </pre>
            <p class="tip">注意：images和masks中的文件名需要一一对应</p>
          </div>
        </el-collapse-item>

        <el-collapse-item title="4. 常见问题" name="4">
          <div class="guide-content">
            <h4>4.1 上传数据集失败</h4>
            <p>请检查数据集文件格式是否正确（支持zip格式），文件大小是否超过系统限制。</p>

            <h4>4.2 模型训练时间过长</h4>
            <p>模型训练时间取决于数据集大小、模型复杂度和硬件性能。请耐心等待，训练过程中不要关闭浏览器。</p>

            <h4>4.3 分割结果不理想</h4>
            <p>请尝试使用不同的模型或调整训练参数，也可以上传更多的训练数据来提高模型性能。</p>

            <h4>4.4 找不到已训练的模型</h4>
            <p>请在"模型训练"页面确认模型状态显示为"已完成"，只有训练完成的模型才能用于分割和评估。</p>
          </div>
        </el-collapse-item>

        <el-collapse-item title="5. 技术支持" name="5">
          <div class="guide-content">
            <p>如果您在使用过程中遇到任何问题，请联系技术支持：</p>
            <ul>
              <li>邮箱：support@medical-segmentation.com</li>
              <li>电话：123-4567-8910</li>
              <li>工作时间：周一至周五 9:00-18:00</li>
            </ul>
          </div>
        </el-collapse-item>
      </el-collapse>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const activeNames = ref(['1'])
</script>

<style scoped>
.guide-view {
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

.guide-card {
  margin-top: 20px;
}

.guide-content {
  padding: 10px 20px;
  line-height: 1.8;
  color: #606266;
}

.guide-content h4 {
  margin-top: 20px;
  margin-bottom: 10px;
  color: #303133;
}

.guide-content ul {
  margin-left: 20px;
}

.guide-content li {
  margin-bottom: 8px;
}

.guide-content p {
  margin-bottom: 10px;
}

.tip {
  color: #e6a23c;
  font-size: 13px;
  padding: 8px 12px;
  background-color: #fdf6ec;
  border-radius: 4px;
  margin-top: 10px;
}

.code-block {
  background-color: #1e1e1e;
  color: #d4d4d4;
  padding: 15px;
  border-radius: 6px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  overflow-x: auto;
  margin: 15px 0;
}
</style>
