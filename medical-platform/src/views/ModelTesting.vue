<template>
  <div class="testing-view">
    <div class="header">
      <h2>模型评估</h2>
    </div>

    <el-row :gutter="20">
      <el-col :span="8">
        <el-card class="config-card">
          <template #header>
            <div class="card-header">
              <span>评估配置</span>
            </div>
          </template>

          <el-form :model="testingForm" label-width="100px">
            <el-form-item label="选择模型">
              <el-select v-model="testingForm.modelId" placeholder="请选择模型" style="width: 100%;">
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
            <el-form-item label="待评估图片">
              <el-upload
                class="image-upload"
                ref="imageUploadRef"
                action="#"
                :auto-upload="false"
                :on-change="(file) => handleImageChange(file, 'image')"
                :limit="1"
                accept="image/*"
                list-type="picture"
              >
                <el-button type="primary">
                  <el-icon><Upload /></el-icon>
                  选择图片
                </el-button>
              </el-upload>
            </el-form-item>
            <el-form-item label="标签图片">
              <el-upload
                class="image-upload"
                ref="labelUploadRef"
                action="#"
                :auto-upload="false"
                :on-change="(file) => handleImageChange(file, 'label')"
                :limit="1"
                accept="image/*"
                list-type="picture"
              >
                <el-button type="primary">
                  <el-icon><Upload /></el-icon>
                  选择图片
                </el-button>
              </el-upload>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="startTesting" :loading="isTesting" :disabled="!canEvaluate">
                <el-icon><Aim /></el-icon>
                开始评估
              </el-button>
              <el-button @click="resetForm">重置</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :span="16">
        <el-card class="result-card">
          <template #header>
            <div class="card-header">
              <span>评估结果</span>
              <el-tag v-if="evaluationResult" type="success">已完成</el-tag>
            </div>
          </template>

          <div v-if="evaluationResult" class="evaluation-content">
            <!-- 评估指标 -->
            <div class="metrics-grid">
              <div class="metric-box">
                <div class="metric-label">准确率 (Accuracy)</div>
                <div class="metric-value accuracy">{{ metrics.accuracy }}</div>
              </div>
              <div class="metric-box">
                <div class="metric-label">精确率 (Precision)</div>
                <div class="metric-value precision">{{ metrics.precision }}</div>
              </div>
              <div class="metric-box">
                <div class="metric-label">召回率 (Recall)</div>
                <div class="metric-value recall">{{ metrics.recall }}</div>
              </div>
              <div class="metric-box">
                <div class="metric-label">F1分数</div>
                <div class="metric-value f1">{{ metrics.f1_score }}</div>
              </div>
              <div class="metric-box">
                <div class="metric-label">IoU</div>
                <div class="metric-value iou">{{ metrics.iou }}</div>
              </div>
              <div class="metric-box">
                <div class="metric-label">Dice</div>
                <div class="metric-value dice">{{ metrics.dice }}</div>
              </div>
            </div>

            <!-- 图片对比 -->
            <div class="image-comparison">
              <div class="image-item">
                <div class="image-title">原始图片</div>
                <div class="image-container">
                  <img v-if="imageUrl" :src="imageUrl" class="result-image" />
                </div>
              </div>
              <div class="image-item">
                <div class="image-title">标签图片</div>
                <div class="image-container">
                  <img v-if="labelUrl" :src="labelUrl" class="result-image" />
                </div>
              </div>
              <div class="image-item">
                <div class="image-title">预测结果</div>
                <div class="image-container">
                  <img v-if="predictionUrl" :src="predictionUrl" class="result-image" />
                </div>
              </div>
            </div>

            <!-- 反馈区域 -->
            <div class="feedback-section">
              <div class="feedback-header">
                <span>评估反馈</span>
                <el-rate v-model="feedbackScore" :colors="['#99A9BF', '#F7BA2A', '#FF9900']"></el-rate>
              </div>
              <el-input v-model="feedbackText" type="textarea" :rows="3" placeholder="请输入评估反馈"></el-input>
              <el-button type="primary" @click="submitFeedback" style="margin-top: 10px;">
                提交反馈
              </el-button>
            </div>
          </div>

          <div v-else class="no-result">
            <el-empty description="暂无评估结果，请先进行评估">
              <el-button type="primary" @click="startTesting" :loading="isTesting" :disabled="!canEvaluate">开始评估</el-button>
            </el-empty>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 评估历史 -->
    <el-card class="history-card" style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>评估历史</span>
        </div>
      </template>

      <el-table :data="evaluationHistory" v-loading="loadingHistory" style="width: 100%">
        <el-table-column prop="id" label="ID" width="60"></el-table-column>
        <el-table-column prop="modelName" label="模型名称" min-width="150"></el-table-column>
        <el-table-column prop="imageName" label="图片名称" min-width="150"></el-table-column>
        <el-table-column prop="accuracy" label="准确率" width="100"></el-table-column>
        <el-table-column prop="iou" label="IoU" width="100"></el-table-column>
        <el-table-column prop="created_at" label="评估时间" width="160"></el-table-column>
      </el-table>

      <el-empty v-if="!loadingHistory && evaluationHistory.length === 0" description="暂无评估历史"></el-empty>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Upload, Aim } from '@element-plus/icons-vue'
import { modelAPI, evaluateAPI, feedbackAPI } from '../api/index'

const availableModels = ref([])
const evaluationHistory = ref([])
const loadingHistory = ref(false)
const isTesting = ref(false)
const evaluationResult = ref(false)
const imageUrl = ref('')
const labelUrl = ref('')
const predictionUrl = ref('')
const feedbackScore = ref(5)
const feedbackText = ref('')
const imageUploadRef = ref(null)
const labelUploadRef = ref(null)

const userInfo = computed(() => {
  const user = localStorage.getItem('user')
  return user ? JSON.parse(user) : null
})

const canEvaluate = computed(() => {
  return testingForm.modelId && imageFile.value && labelFile.value
})

const testingForm = reactive({
  modelId: '',
  image: null,
  label: null
})

const imageFile = ref(null)
const labelFile = ref(null)

const metrics = reactive({
  accuracy: '0%',
  precision: '0%',
  recall: '0%',
  f1_score: '0%',
  iou: '0%',
  dice: '0%'
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
    const res = await evaluateAPI.getHistory(userInfo.value?.user_id)
    if (res.success) {
      evaluationHistory.value = res.history
    }
  } catch (error) {
    ElMessage.error('获取评估历史失败')
  } finally {
    loadingHistory.value = false
  }
}

const handleImageChange = (file, type) => {
  if (type === 'image') {
    imageFile.value = file.raw
    imageUrl.value = URL.createObjectURL(file.raw)
  } else {
    labelFile.value = file.raw
    labelUrl.value = URL.createObjectURL(file.raw)
  }
}

const startTesting = async () => {
  if (!testingForm.modelId || !imageFile.value || !labelFile.value) {
    ElMessage.error('请选择模型、上传待评估图片和标签图片')
    return
  }

  isTesting.value = true
  evaluationResult.value = false

  try {
    const formData = new FormData()
    formData.append('model_id', testingForm.modelId)
    formData.append('user_id', userInfo.value?.user_id)
    formData.append('image', imageFile.value)
    formData.append('label', labelFile.value)

    const res = await evaluateAPI.evaluate(formData)

    if (res.success) {
      // 更新指标
      const m = res.metrics
      metrics.accuracy = m.accuracy
      metrics.precision = m.precision
      metrics.recall = m.recall
      metrics.f1_score = m.f1_score
      metrics.iou = m.iou
      metrics.dice = m.dice

      // 设置预测结果图片
      predictionUrl.value = `data:image/png;base64,${res.result_image}`

      evaluationResult.value = true
      ElMessage.success('模型评估成功')
      fetchHistory()
    }
  } catch (error) {
    ElMessage.error(error.message || '模型评估失败')
  } finally {
    isTesting.value = false
  }
}

const submitFeedback = async () => {
  if (!feedbackText.value) {
    ElMessage.warning('请输入反馈内容')
    return
  }

  try {
    const res = await feedbackAPI.submit({
      model_id: testingForm.modelId,
      feedback: feedbackText.value,
      score: feedbackScore.value,
      user_id: userInfo.value?.user_id
    })

    if (res.success) {
      ElMessage.success('反馈提交成功')
      feedbackText.value = ''
      feedbackScore.value = 5
    }
  } catch (error) {
    ElMessage.error('反馈提交失败')
  }
}

const resetForm = () => {
  testingForm.modelId = ''
  imageFile.value = null
  labelFile.value = null
  imageUrl.value = ''
  labelUrl.value = ''
  predictionUrl.value = ''
  evaluationResult.value = false
  feedbackText.value = ''
  feedbackScore.value = 5
  if (imageUploadRef.value) imageUploadRef.value.clearFiles()
  if (labelUploadRef.value) labelUploadRef.value.clearFiles()
}

onMounted(() => {
  fetchModels()
  fetchHistory()
})
</script>

<style scoped>
.testing-view {
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

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 15px;
  margin-bottom: 20px;
}

.metric-box {
  text-align: center;
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 8px;
}

.metric-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
}

.metric-value {
  font-size: 20px;
  font-weight: bold;
  color: #409eff;
}

.image-comparison {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  margin: 20px 0;
}

.image-item {
  flex: 1;
  text-align: center;
}

.image-title {
  font-size: 14px;
  color: #606266;
  margin-bottom: 10px;
}

.image-container {
  display: flex;
  justify-content: center;
}

.result-image {
  max-width: 100%;
  max-height: 200px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
}

.feedback-section {
  margin-top: 20px;
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 8px;
}

.feedback-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.no-result {
  text-align: center;
  padding: 60px 0;
}
</style>
