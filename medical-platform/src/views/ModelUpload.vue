<template>
  <div class="upload-view">
    <div class="header">
      <h2>上传模型</h2>
    </div>

    <el-row :gutter="20">
      <!-- 上传表单 -->
      <el-col :span="14">
        <el-card class="upload-card">
          <template #header>
            <div class="card-header">
              <span>上传新模型</span>
            </div>
          </template>

          <el-form :model="uploadForm" label-width="100px">
            <el-form-item label="模型名称">
              <el-input v-model="uploadForm.name" placeholder="请输入模型名称（可选）"></el-input>
            </el-form-item>

            <el-form-item label="模型描述">
              <el-input v-model="uploadForm.description" type="textarea" :rows="3" placeholder="请输入模型描述（可选）"></el-input>
            </el-form-item>

            <el-form-item label="模型类型">
              <el-select v-model="uploadForm.type" placeholder="请选择模型类型" style="width: 100%;">
                <el-option label="U-Net" value="unet"></el-option>
                <el-option label="U-Net++" value="unet++"></el-option>
                <el-option label="ResU-Net" value="resunet"></el-option>
                <el-option label="DeepLabV3" value="deeplabv3"></el-option>
                <el-option label="其他" value="other"></el-option>
              </el-select>
            </el-form-item>

            <el-form-item label="关联数据集">
              <el-select v-model="uploadForm.datasetId" placeholder="请选择关联的数据集（可选）" clearable style="width: 100%;">
                <el-option v-for="dataset in datasets" :key="dataset.id" :label="dataset.name" :value="dataset.id"></el-option>
              </el-select>
            </el-form-item>

            <el-form-item label="模型文件">
              <el-upload
                ref="uploadRef"
                class="model-uploader"
                :action="uploadUrl"
                :headers="uploadHeaders"
                :data="uploadData"
                :auto-upload="false"
                :on-change="handleFileChange"
                :on-success="handleSuccess"
                :on-error="handleError"
                :on-progress="handleProgress"
                drag
                accept=".pth,.pt,.h5,.onnx,.pb,.tflite"
                limit="1"
              >
                <el-icon class="el-icon--upload"><upload-filled /></el-icon>
                <div class="el-upload__text">
                  拖拽文件到此处或 <em>点击上传</em>
                </div>
                <template #tip>
                  <div class="el-upload__tip">
                    支持格式: .pth, .pt, .h5, .onnx, .pb, .tflite
                  </div>
                </template>
              </el-upload>
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="submitUpload" :loading="uploading" :disabled="!selectedFile">
                <el-icon><Upload /></el-icon>
                {{ uploading ? '上传中...' : '开始上传' }}
              </el-button>
              <el-button @click="resetForm">重置</el-button>
            </el-form-item>
          </el-form>

          <!-- 上传进度 -->
          <el-progress v-if="uploadProgress > 0" :percentage="uploadProgress" :status="uploadProgress === 100 ? 'success' : ''" />
        </el-card>
      </el-col>

      <!-- 已上传模型列表 -->
      <el-col :span="10">
        <el-card class="model-list-card">
          <template #header>
            <div class="card-header">
              <span>已上传的模型</span>
              <el-button type="primary" link @click="loadModels">刷新</el-button>
            </div>
          </template>

          <div v-if="models.length === 0" class="empty-state">
            <el-empty description="暂无已上传的模型" />
          </div>

          <div v-else class="model-list">
            <div v-for="model in models" :key="model.id" class="model-item">
              <div class="model-info">
                <el-icon><Document /></el-icon>
                <span class="model-name">{{ model.name }}</span>
                <el-tag size="small" :type="getStatusType(model.status)">{{ model.status }}</el-tag>
              </div>
              <div class="model-meta">
                <span class="model-type">{{ model.type }}</span>
                <span class="model-date">{{ model.created_at }}</span>
              </div>
              <div class="model-actions">
                <el-button type="primary" link size="small" @click="useModel(model)">使用</el-button>
                <el-button type="danger" link size="small" @click="deleteModel(model)">删除</el-button>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled, Document, Upload } from '@element-plus/icons-vue'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api'

const uploadRef = ref(null)
const uploadForm = ref({
  name: '',
  description: '',
  type: 'unet',
  datasetId: null
})
const selectedFile = ref(null)
const uploading = ref(false)
const uploadProgress = ref(0)
const datasets = ref([])
const models = ref([])

const user = computed(() => {
  try {
    return JSON.parse(localStorage.getItem('user') || '{}')
  } catch {
    return {}
  }
})

const uploadUrl = computed(() => `${API_BASE}/models/upload`)
const uploadHeaders = computed(() => ({
  // 可添加认证头
}))

const uploadData = computed(() => ({
  name: uploadForm.value.name,
  description: uploadForm.value.description,
  type: uploadForm.value.type,
  dataset_id: uploadForm.value.datasetId,
  user_id: user.value.id || 1
}))

// 加载数据集列表
const loadDatasets = async () => {
  try {
    const res = await fetch(`${API_BASE}/datasets?user_id=${user.value.id || 1}`)
    const data = await res.json()
    if (data.success) {
      datasets.value = data.datasets || []
    }
  } catch (e) {
    console.error('加载数据集失败:', e)
  }
}

// 加载模型列表
const loadModels = async () => {
  try {
    const res = await fetch(`${API_BASE}/models?user_id=${user.value.id || 1}`)
    const data = await res.json()
    if (data.success) {
      // 过滤出已上传的模型（状态为 uploaded 或已有 model_path）
      models.value = (data.models || []).filter(m => m.status === 'uploaded')
    }
  } catch (e) {
    console.error('加载模型失败:', e)
  }
}

// 文件选择
const handleFileChange = (file) => {
  selectedFile.value = file.raw
  // 如果没有输入名称，使用文件名
  if (!uploadForm.value.name) {
    uploadForm.value.name = file.name.replace(/\.[^/.]+$/, '')
  }
}

// 上传成功
const handleSuccess = (response) => {
  uploading.value = false
  uploadProgress.value = 100
  ElMessage.success('模型上传成功')
  resetForm()
  loadModels()
}

// 上传失败
const handleError = (err) => {
  uploading.value = false
  uploadProgress.value = 0
  ElMessage.error('模型上传失败: ' + (err.message || '未知错误'))
}

// 上传进度
const handleProgress = (event) => {
  uploadProgress.value = Math.round(event.percent || 0)
}

// 提交上传
const submitUpload = () => {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择模型文件')
    return
  }
  uploading.value = true
  uploadProgress.value = 0
  uploadRef.value?.submit()
}

// 重置表单
const resetForm = () => {
  uploadForm.value = {
    name: '',
    description: '',
    type: 'unet',
    datasetId: null
  }
  selectedFile.value = null
  uploadProgress.value = 0
  if (uploadRef.value) {
    uploadRef.value.clearFiles()
  }
}

// 获取状态类型
const getStatusType = (status) => {
  const types = {
    uploaded: 'success',
    training: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return types[status] || 'info'
}

// 使用模型
const useModel = (model) => {
  ElMessage.info(`已选择模型: ${model.name}`)
  // 可以导航到分割页面使用该模型
}

// 删除模型
const deleteModel = async (model) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除模型 "${model.name}" 吗？`,
      '确认删除',
      { type: 'warning' }
    )

    const res = await fetch(`${API_BASE}/models/${model.id}`, {
      method: 'DELETE'
    })
    const data = await res.json()

    if (data.success) {
      ElMessage.success('模型删除成功')
      loadModels()
    } else {
      ElMessage.error(data.message || '删除失败')
    }
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  loadDatasets()
  loadModels()
})
</script>

<style scoped>
.upload-view {
  padding: 20px;
}

.header {
  margin-bottom: 20px;
}

.header h2 {
  margin: 0;
  color: #303133;
}

.upload-card {
  margin-bottom: 20px;
}

.model-uploader {
  width: 100%;
}

.model-list-card {
  max-height: calc(100vh - 200px);
  overflow-y: auto;
}

.empty-state {
  padding: 40px 0;
}

.model-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.model-item {
  padding: 12px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  transition: all 0.3s;
}

.model-item:hover {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.15);
}

.model-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.model-name {
  font-weight: 500;
  color: #303133;
  flex: 1;
}

.model-meta {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
}

.model-actions {
  display: flex;
  gap: 8px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
