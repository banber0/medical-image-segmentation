<template>
  <div class="history-view">
    <div class="header">
      <h2>历史记录</h2>
    </div>

    <el-card class="history-card">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="分割历史" name="segmentation">
          <el-table :data="segmentationHistory" v-loading="loadingSeg" style="width: 100%">
            <el-table-column prop="id" label="ID" width="60"></el-table-column>
            <el-table-column prop="modelName" label="模型名称" min-width="150"></el-table-column>
            <el-table-column prop="imageName" label="图片名称" min-width="150"></el-table-column>
            <el-table-column prop="created_at" label="分割时间" width="160"></el-table-column>
            <el-table-column label="操作" width="100">
              <template #default="scope">
                <el-button size="small" type="primary" @click="viewSegmentationResult(scope.row)">查看</el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!loadingSeg && segmentationHistory.length === 0" description="暂无分割历史"></el-empty>
        </el-tab-pane>

        <el-tab-pane label="训练历史" name="training">
          <el-table :data="trainingHistory" v-loading="loadingTrain" style="width: 100%">
            <el-table-column prop="id" label="ID" width="60"></el-table-column>
            <el-table-column prop="modelName" label="模型名称" min-width="150"></el-table-column>
            <el-table-column prop="datasetName" label="数据集名称" min-width="150"></el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template #default="scope">
                <el-tag :type="getStatusType(scope.row.status)">{{ getStatusText(scope.row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="训练时间" width="160"></el-table-column>
            <el-table-column label="操作" width="100">
              <template #default="scope">
                <el-button size="small" @click="viewTrainingDetail(scope.row)">查看</el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!loadingTrain && trainingHistory.length === 0" description="暂无训练历史"></el-empty>
        </el-tab-pane>

        <el-tab-pane label="评估历史" name="evaluation">
          <el-table :data="evaluationHistory" v-loading="loadingEval" style="width: 100%">
            <el-table-column prop="id" label="ID" width="60"></el-table-column>
            <el-table-column prop="modelName" label="模型名称" min-width="150"></el-table-column>
            <el-table-column prop="imageName" label="图片名称" min-width="150"></el-table-column>
            <el-table-column prop="accuracy" label="准确率" width="100"></el-table-column>
            <el-table-column prop="iou" label="IoU" width="100"></el-table-column>
            <el-table-column prop="created_at" label="评估时间" width="160"></el-table-column>
            <el-table-column label="操作" width="100">
              <template #default="scope">
                <el-button size="small" @click="viewEvaluationDetail(scope.row)">查看</el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!loadingEval && evaluationHistory.length === 0" description="暂无评估历史"></el-empty>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 分割结果对话框 -->
    <el-dialog v-model="showSegDialog" title="分割结果详情" width="800px">
      <div class="result-dialog">
        <div class="result-item">
          <h4>原始图片</h4>
          <div class="image-box">
            <img v-if="selectedSeg.imageUrl" :src="selectedSeg.imageUrl" class="result-image" />
            <el-empty v-else description="暂无图片" :image-size="100"></el-empty>
          </div>
        </div>
        <div class="result-item">
          <h4>分割结果</h4>
          <div class="image-box">
            <img v-if="selectedSeg.resultUrl" :src="selectedSeg.resultUrl" class="result-image" />
            <el-empty v-else description="暂无结果" :image-size="100"></el-empty>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- 训练详情对话框 -->
    <el-dialog v-model="showTrainDialog" title="训练详情" width="500px">
      <el-descriptions :column="1" border>
        <el-descriptions-item label="模型名称">{{ selectedTrain.modelName }}</el-descriptions-item>
        <el-descriptions-item label="数据集名称">{{ selectedTrain.datasetName }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(selectedTrain.status)">{{ getStatusText(selectedTrain.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="训练时间">{{ selectedTrain.created_at }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <!-- 评估详情对话框 -->
    <el-dialog v-model="showEvalDialog" title="评估详情" width="500px">
      <el-descriptions :column="1" border>
        <el-descriptions-item label="模型名称">{{ selectedEval.modelName }}</el-descriptions-item>
        <el-descriptions-item label="图片名称">{{ selectedEval.imageName }}</el-descriptions-item>
        <el-descriptions-item label="准确率">{{ selectedEval.accuracy }}</el-descriptions-item>
        <el-descriptions-item label="精确率">{{ selectedEval.precision }}</el-descriptions-item>
        <el-descriptions-item label="召回率">{{ selectedEval.recall }}</el-descriptions-item>
        <el-descriptions-item label="F1分数">{{ selectedEval.f1_score }}</el-descriptions-item>
        <el-descriptions-item label="IoU">{{ selectedEval.iou }}</el-descriptions-item>
        <el-descriptions-item label="Dice">{{ selectedEval.dice }}</el-descriptions-item>
        <el-descriptions-item label="评估时间">{{ selectedEval.created_at }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { segmentationAPI, trainingAPI, evaluateAPI } from '../api/index'

const activeTab = ref('segmentation')

const segmentationHistory = ref([])
const trainingHistory = ref([])
const evaluationHistory = ref([])
const loadingSeg = ref(false)
const loadingTrain = ref(false)
const loadingEval = ref(false)

const showSegDialog = ref(false)
const showTrainDialog = ref(false)
const showEvalDialog = ref(false)

const selectedSeg = reactive({ imageUrl: '', resultUrl: '' })
const selectedTrain = reactive({ modelName: '', datasetName: '', status: '', created_at: '' })
const selectedEval = reactive({ modelName: '', imageName: '', accuracy: '', precision: '', recall: '', f1_score: '', iou: '', dice: '', created_at: '' })

const userInfo = computed(() => {
  const user = localStorage.getItem('user')
  return user ? JSON.parse(user) : null
})

const getStatusType = (status) => {
  const types = { completed: 'success', running: 'warning', failed: 'danger', pending: 'info' }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = { completed: '已完成', running: '进行中', failed: '失败', pending: '等待中' }
  return texts[status] || status
}

const fetchSegmentationHistory = async () => {
  loadingSeg.value = true
  try {
    const res = await segmentationAPI.getHistory(userInfo.value?.user_id)
    if (res.success) {
      segmentationHistory.value = res.history
    }
  } catch (error) {
    ElMessage.error('获取分割历史失败')
  } finally {
    loadingSeg.value = false
  }
}

const fetchTrainingHistory = async () => {
  loadingTrain.value = true
  try {
    const res = await trainingAPI.getHistory(userInfo.value?.user_id)
    if (res.success) {
      trainingHistory.value = res.history
    }
  } catch (error) {
    ElMessage.error('获取训练历史失败')
  } finally {
    loadingTrain.value = false
  }
}

const fetchEvaluationHistory = async () => {
  loadingEval.value = true
  try {
    const res = await evaluateAPI.getHistory(userInfo.value?.user_id)
    if (res.success) {
      evaluationHistory.value = res.history
    }
  } catch (error) {
    ElMessage.error('获取评估历史失败')
  } finally {
    loadingEval.value = false
  }
}

const viewSegmentationResult = async (row) => {
  selectedSeg.imageUrl = ''
  selectedSeg.resultUrl = ''
  showSegDialog.value = true
  try {
    const res = await segmentationAPI.getHistoryDetail(row.id)
    if (res.success && res.detail) {
      selectedSeg.imageUrl = res.detail.imageData ? `data:image/png;base64,${res.detail.imageData}` : ''
      selectedSeg.resultUrl = res.detail.resultData ? `data:image/png;base64,${res.detail.resultData}` : ''
    }
  } catch (error) {
    ElMessage.error('获取分割详情失败')
  }
}

const viewTrainingDetail = (row) => {
  selectedTrain.modelName = row.modelName
  selectedTrain.datasetName = row.datasetName
  selectedTrain.status = row.status
  selectedTrain.created_at = row.created_at
  showTrainDialog.value = true
}

const viewEvaluationDetail = (row) => {
  selectedEval.modelName = row.modelName
  selectedEval.imageName = row.imageName
  selectedEval.accuracy = row.accuracy
  selectedEval.precision = row.precision || '-'
  selectedEval.recall = row.recall || '-'
  selectedEval.f1_score = row.f1_score || '-'
  selectedEval.iou = row.iou
  selectedEval.dice = row.dice || '-'
  selectedEval.created_at = row.created_at
  showEvalDialog.value = true
}

const fetchAll = () => {
  fetchSegmentationHistory()
  fetchTrainingHistory()
  fetchEvaluationHistory()
}

watch(activeTab, (val) => {
  if (val === 'segmentation') fetchSegmentationHistory()
  if (val === 'training') fetchTrainingHistory()
  if (val === 'evaluation') fetchEvaluationHistory()
})

onMounted(() => {
  fetchAll()
})
</script>

<style scoped>
.history-view {
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

.history-card {
  margin-top: 20px;
}

.result-dialog {
  display: flex;
  gap: 20px;
}

.result-item {
  flex: 1;
  text-align: center;
}

.result-item h4 {
  margin-bottom: 10px;
  color: #606266;
}

.image-box {
  min-height: 300px;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #f5f7fa;
  border-radius: 8px;
}

.result-image {
  max-width: 100%;
  max-height: 300px;
  object-fit: contain;
}
</style>
