<template>
  <div class="segmentation-view">
    <div class="header">
      <h2>影像分割</h2>
    </div>

    <el-row :gutter="20">
      <el-col :span="6">
        <el-card class="config-card">
          <template #header>
            <div class="card-header">
              <span>分割配置</span>
            </div>
          </template>

          <el-form :model="segmentationForm" label-width="100px">
            <el-form-item label="选择模型">
              <el-select v-model="segmentationForm.modelId" placeholder="请选择模型" style="width: 100%;">
                <el-option
                  v-for="model in availableModels"
                  :key="model.id"
                  :label="model.name"
                  :value="model.id"
                  :disabled="!model.model_path"
                >
                  <span>{{ model.name }}</span>
                  <span style="float: right; color: #8492a6; font-size: 12px;">
                    {{ model.status === 'completed' ? '已训练' : '已上传' }}
                  </span>
                </el-option>
              </el-select>
            </el-form-item>
            <el-form-item label="待分割图片">
              <el-upload
                class="image-upload"
                ref="imageUploadRef"
                action="#"
                :auto-upload="false"
                :on-change="handleImageChange"
                :limit="1"
                accept="image/*"
                drag
              >
                <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
                <div class="el-upload__text">
                  将图片拖到此处，或<em>点击上传</em>
                </div>
              </el-upload>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="startSegmentation" :loading="isSegmenting" :disabled="!canSegment">
                <el-icon><Operation /></el-icon>
                开始分割
              </el-button>
              <el-button @click="resetForm">清除</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :span="18">
        <el-card class="result-card">
          <template #header>
            <div class="card-header">
              <span>分割结果</span>
            </div>
          </template>

          <div class="image-comparison">
            <div class="image-section">
              <div class="image-title">原始图片</div>
              <div class="image-container">
                <div v-if="!imageUrl" class="image-placeholder">
                  <el-icon :size="60" color="#c0c4cc"><Picture /></el-icon>
                  <p>请上传待分割图片</p>
                </div>
                <img v-else :src="imageUrl" class="result-image" />
              </div>
            </div>

            <div class="image-section">
              <div class="image-title">分割结果</div>
              <div class="image-container">
                <div v-if="!segmentationResult" class="image-placeholder">
                  <el-icon :size="60" color="#c0c4cc"><Picture /></el-icon>
                  <p>分割结果将显示在这里</p>
                </div>
                <img v-else :src="segmentationResult" class="result-image" />
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 分割历史 -->
    <el-card class="history-card" style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>分割历史记录</span>
        </div>
      </template>

      <el-table :data="segmentationHistory" v-loading="loadingHistory" style="width: 100%">
        <el-table-column prop="id" label="ID" width="60"></el-table-column>
        <el-table-column prop="modelName" label="模型名称" min-width="150"></el-table-column>
        <el-table-column prop="imageName" label="图片名称" min-width="150"></el-table-column>
        <el-table-column prop="created_at" label="分割时间" width="160"></el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="scope">
            <el-button size="small" type="primary" @click="viewHistoryResult(scope.row)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!loadingHistory && segmentationHistory.length === 0" description="暂无分割历史"></el-empty>
    </el-card>

    <!-- 查看历史结果对话框 -->
    <el-dialog v-model="showHistoryDialog" title="历史分割结果" width="900px">
      <div class="history-dialog">
        <div class="history-item">
          <div class="image-title">原始图片</div>
          <div class="image-container">
            <img v-if="selectedHistory.imageUrl" :src="selectedHistory.imageUrl" class="result-image" />
          </div>
        </div>
        <div class="history-item">
          <div class="image-title">分割结果</div>
          <div class="image-container">
            <img v-if="selectedHistory.resultUrl" :src="selectedHistory.resultUrl" class="result-image" />
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="showHistoryDialog = false">关闭</el-button>
        <el-button type="primary" @click="downloadHistoryResult">下载结果</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled, Picture, Operation } from '@element-plus/icons-vue'
import { modelAPI, segmentationAPI } from '../api/index'

const availableModels = ref([])
const segmentationHistory = ref([])
const loadingHistory = ref(false)
const isSegmenting = ref(false)
const imageUrl = ref('')
const segmentationResult = ref('')
const imageUploadRef = ref(null)
const showHistoryDialog = ref(false)

const userInfo = computed(() => {
  const user = localStorage.getItem('user')
  return user ? JSON.parse(user) : null
})

const canSegment = computed(() => {
  return segmentationForm.modelId && imageFile.value
})

const segmentationForm = reactive({
  modelId: '',
  image: null
})

const imageFile = ref(null)

const selectedHistory = reactive({
  id: '',
  imageUrl: '',
  resultUrl: ''
})

const fetchModels = async () => {
  try {
    const res = await modelAPI.getList(userInfo.value?.user_id)
    if (res.success) {
      // 同时显示已训练(completed)和已上传(uploaded)的模型
      availableModels.value = res.models.filter(m =>
        m.status === 'completed' || m.status === 'uploaded'
      )
    }
  } catch (error) {
    ElMessage.error('获取模型列表失败')
  }
}

const fetchHistory = async () => {
  loadingHistory.value = true
  try {
    const res = await segmentationAPI.getHistory(userInfo.value?.user_id)
    if (res.success) {
      segmentationHistory.value = res.history
    }
  } catch (error) {
    ElMessage.error('获取分割历史失败')
  } finally {
    loadingHistory.value = false
  }
}

const handleImageChange = (file) => {
  imageFile.value = file.raw
  imageUrl.value = URL.createObjectURL(file.raw)
  segmentationResult.value = ''
}

const startSegmentation = async () => {
  if (!segmentationForm.modelId || !imageFile.value) {
    ElMessage.error('请选择模型并上传图片')
    return
  }

  isSegmenting.value = true
  segmentationResult.value = ''

  try {
    const formData = new FormData()
    formData.append('model_id', segmentationForm.modelId)
    formData.append('user_id', userInfo.value?.user_id)
    formData.append('image', imageFile.value)

    const res = await segmentationAPI.segment(formData)

    if (res.success) {
      // 设置分割结果图片
      segmentationResult.value = `data:image/png;base64,${res.result_image}`
      ElMessage.success('影像分割成功')
      fetchHistory()
    }
  } catch (error) {
    ElMessage.error(error.message || '影像分割失败')
  } finally {
    isSegmenting.value = false
  }
}

const viewHistoryResult = async (row) => {
  selectedHistory.id = row.id
  selectedHistory.imageUrl = ''
  selectedHistory.resultUrl = ''
  showHistoryDialog.value = true

  // 异步获取历史详情
  try {
    const res = await segmentationAPI.getHistoryDetail(row.id)
    if (res.success && res.detail) {
      selectedHistory.imageUrl = res.detail.imageData ? `data:image/png;base64,${res.detail.imageData}` : ''
      selectedHistory.resultUrl = res.detail.resultData ? `data:image/png;base64,${res.detail.resultData}` : ''
    }
  } catch (error) {
    ElMessage.error('获取历史详情失败')
  }
}

const downloadHistoryResult = () => {
  if (selectedHistory.resultUrl) {
    const link = document.createElement('a')
    link.href = selectedHistory.resultUrl
    link.download = 'segmentation_result.png'
    link.click()
  } else {
    ElMessage.warning('无法下载')
  }
}

const resetForm = () => {
  segmentationForm.modelId = ''
  imageFile.value = null
  imageUrl.value = ''
  segmentationResult.value = ''
  if (imageUploadRef.value) imageUploadRef.value.clearFiles()
}

onMounted(() => {
  fetchModels()
  fetchHistory()
})
</script>

<style scoped>
.segmentation-view {
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

.config-card, .result-card, .history-card {
  height: fit-content;
}

.image-upload {
  width: 100%;
}

.image-comparison {
  display: flex;
  gap: 20px;
}

.image-section {
  flex: 1;
}

.image-title {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 15px;
  text-align: center;
}

.image-container {
  min-height: 400px;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #f5f7fa;
  border-radius: 8px;
  overflow: hidden;
}

.image-placeholder {
  text-align: center;
  color: #909399;
}

.image-placeholder p {
  margin-top: 10px;
}

.result-image {
  max-width: 100%;
  max-height: 400px;
  object-fit: contain;
}

.history-dialog {
  display: flex;
  gap: 20px;
}

.history-item {
  flex: 1;
}

.history-item .image-container {
  min-height: 300px;
}
</style>
