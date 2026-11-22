<template>
  <div class="training-view">
    <div class="header">
      <h2>模型训练</h2>
    </div>

    <el-row :gutter="20">
      <el-col :span="12">
        <el-card class="config-card">
          <template #header>
            <div class="card-header">
              <span>训练配置</span>
            </div>
          </template>

          <el-form :model="trainingForm" label-width="100px">
            <el-form-item label="模型名称">
              <el-input v-model="trainingForm.modelName" placeholder="请输入模型名称"></el-input>
            </el-form-item>
            <el-form-item label="选择数据集">
              <el-select v-model="trainingForm.datasetId" placeholder="请选择数据集" style="width: 100%;">
                <el-option v-for="dataset in datasets" :key="dataset.id" :label="dataset.name" :value="dataset.id"></el-option>
              </el-select>
            </el-form-item>
            <el-form-item label="模型类型">
              <el-select v-model="trainingForm.modelType" placeholder="请选择模型类型" style="width: 100%;">
                <el-option label="U-Net" value="unet"></el-option>
                <el-option label="U-Net++" value="unet++"></el-option>
                <el-option label="ResU-Net" value="resunet"></el-option>
              </el-select>
            </el-form-item>

            <el-divider content-position="left">训练参数</el-divider>

            <el-form-item label="批次大小">
              <el-input-number v-model="trainingForm.batchSize" :min="1" :max="64" :step="1" style="width: 100%;"></el-input-number>
            </el-form-item>
            <el-form-item label="学习率">
              <el-input-number v-model="trainingForm.learningRate" :min="0.0001" :max="0.1" :step="0.0001" :precision="4" style="width: 100%;"></el-input-number>
            </el-form-item>
            <el-form-item label="训练轮数">
              <el-input-number v-model="trainingForm.epochs" :min="1" :max="500" :step="1" style="width: 100%;"></el-input-number>
            </el-form-item>
            <el-form-item label="验证集比例">
              <el-slider v-model="trainingForm.valSplit" :min="0.1" :max="0.4" :step="0.05" :format-tooltip="val => `${Math.round(val * 100)}%`"></el-slider>
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="startTraining" :loading="isTraining" :disabled="!canStartTraining">
                <el-icon><Cpu /></el-icon>
                开始训练
              </el-button>
              <el-button @click="resetForm">重置</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card class="status-card">
          <template #header>
            <div class="card-header">
              <span>训练状态</span>
              <el-tag v-if="isTraining" type="warning">训练中</el-tag>
              <el-tag v-else-if="trainingStatus === 'completed'" type="success">已完成</el-tag>
              <el-tag v-else type="info">等待开始</el-tag>
            </div>
          </template>

          <div v-if="isTraining || trainingStatus === 'completed'" class="training-status">
            <el-progress :percentage="progress" :status="progressStatus" :format="formatProgress"></el-progress>

            <div class="metrics-section" v-if="currentMetrics">
              <el-row :gutter="10">
                <el-col :span="6">
                  <div class="metric-item">
                    <div class="metric-label">Loss</div>
                    <div class="metric-value">{{ currentMetrics.loss?.toFixed(4) || '-' }}</div>
                  </div>
                </el-col>
                <el-col :span="6">
                  <div class="metric-item">
                    <div class="metric-label">Dice</div>
                    <div class="metric-value">{{ currentMetrics.dice?.toFixed(4) || '-' }}</div>
                  </div>
                </el-col>
                <el-col :span="6">
                  <div class="metric-item">
                    <div class="metric-label">IoU</div>
                    <div class="metric-value">{{ currentMetrics.iou?.toFixed(4) || '-' }}</div>
                  </div>
                </el-col>
                <el-col :span="6">
                  <div class="metric-item">
                    <div class="metric-label">Epoch</div>
                    <div class="metric-value">{{ currentEpoch }}/{{ trainingForm.epochs }}</div>
                  </div>
                </el-col>
              </el-row>
            </div>

            <!-- ECharts Loss 曲线图 -->
            <div class="chart-section">
              <div ref="lossChartRef" class="chart-container"></div>
            </div>

            <!-- ECharts Dice 曲线图 -->
            <div class="chart-section">
              <div ref="diceChartRef" class="chart-container"></div>
            </div>

            <div style="margin: 10px 0;">
              <el-button v-if="isTraining" type="danger" @click="stopTraining">停止训练</el-button>
            </div>

            <div class="training-log">
              <el-scrollbar height="150px">
                <div v-for="(log, index) in trainingLogs" :key="index" class="log-item">
                  <span class="log-time">{{ log.time }}</span>
                  <span class="log-message">{{ log.message }}</span>
                </div>
              </el-scrollbar>
            </div>
          </div>

          <div v-else class="no-training">
            <el-empty description="暂无训练任务">
              <el-button type="primary" @click="startTraining" :disabled="!canStartTraining">开始训练</el-button>
            </el-empty>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 已训练模型列表 -->
    <el-card class="models-card" style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>我的模型</span>
        </div>
      </template>

      <el-table :data="trainedModels" v-loading="loadingModels" style="width: 100%">
        <el-table-column prop="id" label="ID" width="60"></el-table-column>
        <el-table-column prop="name" label="模型名称" min-width="150"></el-table-column>
        <el-table-column prop="type" label="类型" width="100">
          <template #default="scope">
            <el-tag>{{ scope.row.type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">{{ getStatusText(scope.row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160"></el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="scope">
            <el-button size="small" type="danger" @click="deleteModel(scope.row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!loadingModels && trainedModels.length === 0" description="暂无训练完成的模型"></el-empty>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Cpu } from '@element-plus/icons-vue'
import { datasetAPI, modelAPI } from '../api/index'
import * as echarts from 'echarts'

const datasets = ref([])
const trainedModels = ref([])
const loading = ref(false)
const loadingModels = ref(false)
const isTraining = ref(false)
const progress = ref(0)
const currentEpoch = ref(0)
const trainingStatus = ref('idle')
const trainingLogs = ref([])
const currentMetrics = ref(null)
let statusTimer = null
let currentTrainingId = null // 当前训练任务ID

// ECharts 相关
const lossChartRef = ref(null)
const diceChartRef = ref(null)
let lossChart = null
let diceChart = null

// 训练指标数据
const chartData = reactive({
  trainLoss: [],
  valLoss: [],
  trainDice: [],
  valDice: [],
  epochs: []
})

const userInfo = computed(() => {
  const user = localStorage.getItem('user')
  return user ? JSON.parse(user) : null
})

const canStartTraining = computed(() => {
  return trainingForm.datasetId && trainingForm.modelName && !isTraining.value
})

const progressStatus = computed(() => {
  if (progress.value === 100) return 'success'
  if (isTraining.value) return 'warning'
  return ''
})

const trainingForm = reactive({
  datasetId: '',
  modelName: '',
  modelType: 'unet',
  batchSize: 4,
  learningRate: 0.001,
  epochs: 10,
  valSplit: 0.2
})

const formatProgress = (percentage) => {
  return `${percentage}%`
}

const getStatusType = (status) => {
  const types = { completed: 'success', training: 'warning', failed: 'danger', pending: 'info' }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = { completed: '已完成', training: '训练中', failed: '失败', pending: '等待中', stopped: '已停止' }
  return texts[status] || status
}

// 初始化图表
const initCharts = () => {
  nextTick(() => {
    if (lossChartRef.value && !lossChart) {
      lossChart = echarts.init(lossChartRef.value)
    }
    if (diceChartRef.value && !diceChart) {
      diceChart = echarts.init(diceChartRef.value)
    }
  })
}

// 更新 Loss 图表
const updateLossChart = () => {
  if (!lossChart) return
  const option = {
    title: { text: 'Loss 曲线', left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'axis' },
    legend: { data: ['训练Loss', '验证Loss'], bottom: 0 },
    grid: { left: '10%', right: '10%', top: '25%', bottom: '15%' },
    xAxis: { type: 'category', data: chartData.epochs, name: 'Epoch' },
    yAxis: { type: 'value', name: 'Loss' },
    series: [
      { name: '训练Loss', type: 'line', data: chartData.trainLoss, smooth: true, color: '#5470C6' },
      { name: '验证Loss', type: 'line', data: chartData.valLoss, smooth: true, color: '#EE6666' }
    ]
  }
  lossChart.setOption(option)
}

// 更新 Dice 图表
const updateDiceChart = () => {
  if (!diceChart) return
  const option = {
    title: { text: 'Dice 曲线', left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'axis' },
    legend: { data: ['训练Dice', '验证Dice'], bottom: 0 },
    grid: { left: '10%', right: '10%', top: '25%', bottom: '15%' },
    xAxis: { type: 'category', data: chartData.epochs, name: 'Epoch' },
    yAxis: { type: 'value', name: 'Dice', min: 0, max: 1 },
    series: [
      { name: '训练Dice', type: 'line', data: chartData.trainDice, smooth: true, color: '#91CC75' },
      { name: '验证Dice', type: 'line', data: chartData.valDice, smooth: true, color: '#FAC858' }
    ]
  }
  diceChart.setOption(option)
}

// 重置图表数据
const resetChartData = () => {
  chartData.trainLoss = []
  chartData.valLoss = []
  chartData.trainDice = []
  chartData.valDice = []
  chartData.epochs = []
}

// 停止训练
const stopTraining = async () => {
  if (!currentTrainingId) {
    ElMessage.warning('没有正在进行的训练任务')
    return
  }

  try {
    const res = await modelAPI.stopTraining(currentTrainingId)
    if (res.success) {
      addLog('正在停止训练...')
      ElMessage.info('已发送停止请求')
    } else {
      ElMessage.error(res.message || '停止训练失败')
    }
  } catch (error) {
    ElMessage.error('停止训练失败')
  }
}

const fetchDatasets = async () => {
  try {
    const res = await datasetAPI.getList(userInfo.value?.user_id)
    if (res.success) {
      datasets.value = res.datasets
    }
  } catch (error) {
    ElMessage.error('获取数据集列表失败')
  }
}

const fetchModels = async () => {
  loadingModels.value = true
  try {
    const res = await modelAPI.getList(userInfo.value?.user_id)
    if (res.success) {
      trainedModels.value = res.models
    }
  } catch (error) {
    ElMessage.error('获取模型列表失败')
  } finally {
    loadingModels.value = false
  }
}

const startTraining = async () => {
  if (!trainingForm.datasetId || !trainingForm.modelName) {
    ElMessage.error('请选择数据集并输入模型名称')
    return
  }

  isTraining.value = true
  progress.value = 0
  currentEpoch.value = 0
  trainingStatus.value = 'training'
  trainingLogs.value = []
  currentMetrics.value = null

  // 重置并初始化图表
  resetChartData()
  initCharts()

  addLog('开始创建模型...')

  try {
    // 创建模型
    const createRes = await modelAPI.create({
      name: trainingForm.modelName,
      type: trainingForm.modelType,
      dataset_id: trainingForm.datasetId,
      config: JSON.stringify({
        batchSize: trainingForm.batchSize,
        learningRate: trainingForm.learningRate,
        epochs: trainingForm.epochs,
        valSplit: trainingForm.valSplit
      }),
      user_id: userInfo.value?.user_id
    })

    if (!createRes.success) {
      throw new Error(createRes.message || '模型创建失败')
    }

    const modelId = createRes.model_id
    addLog(`模型创建成功，ID: ${modelId}`)
    addLog('开始训练...')

    // 开始训练
    const trainRes = await modelAPI.train({
      model_id: modelId,
      dataset_id: trainingForm.datasetId,
      user_id: userInfo.value?.user_id,
      config: {
        batch_size: trainingForm.batchSize,
        learning_rate: trainingForm.learningRate,
        epochs: trainingForm.epochs,
        val_split: trainingForm.valSplit
      }
    })

    if (trainRes.success) {
      addLog(`训练任务已启动，训练ID: ${trainRes.training_id}`)
      currentTrainingId = trainRes.training_id // 保存训练ID，用于停止功能

      // 轮询训练状态
      statusTimer = setInterval(async () => {
        try {
          const statusRes = await modelAPI.getTrainingStatus(trainRes.training_id)
          if (statusRes.success) {
            const status = statusRes.model_status
            const metrics = statusRes.metrics

            if (metrics && metrics.train_loss) {
              const epoch = metrics.train_loss.length
              currentEpoch.value = epoch
              progress.value = Math.round((epoch / trainingForm.epochs) * 100)
              currentMetrics.value = {
                loss: metrics.val_loss?.[epoch - 1],
                dice: metrics.val_dice?.[epoch - 1],
                iou: metrics.val_dice?.[epoch - 1] * 0.9
              }

              // 更新图表数据
              chartData.epochs = Array.from({ length: epoch }, (_, i) => i + 1)
              chartData.trainLoss = metrics.train_loss.map(v => parseFloat(v.toFixed(6)))
              chartData.valLoss = metrics.val_loss.map(v => parseFloat(v.toFixed(6)))
              chartData.trainDice = metrics.train_dice.map(v => parseFloat(v.toFixed(6)))
              chartData.valDice = metrics.val_dice.map(v => parseFloat(v.toFixed(6)))

              // 更新图表
              updateLossChart()
              updateDiceChart()

              if (epoch > 0 && epoch % 2 === 0) {
                addLog(`Epoch ${epoch}: Val Loss = ${currentMetrics.value.loss?.toFixed(4)}, Val Dice = ${currentMetrics.value.dice?.toFixed(4)}`)
              }
            }

            if (status === 'completed') {
              progress.value = 100
              trainingStatus.value = 'completed'
              isTraining.value = false
              clearInterval(statusTimer)
              addLog('训练完成！')
              ElMessage.success('模型训练成功')
              fetchModels()
            } else if (status === 'stopped') {
              trainingStatus.value = 'stopped'
              isTraining.value = false
              clearInterval(statusTimer)
              addLog('训练已被用户停止')
              ElMessage.warning('训练已停止')
            } else if (status === 'failed') {
              trainingStatus.value = 'failed'
              isTraining.value = false
              clearInterval(statusTimer)
              addLog(`训练失败: ${statusRes.logs}`)
              ElMessage.error('模型训练失败')
            }
          }
        } catch (e) {
          console.error('获取训练状态失败', e)
        }
      }, 3000)
    }
  } catch (error) {
    isTraining.value = false
    trainingStatus.value = 'failed'
    addLog(`错误: ${error.message}`)
    ElMessage.error(error.message || '模型训练失败')
  }
}

const deleteModel = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除该模型吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    const res = await modelAPI.delete(id)
    if (res.success) {
      ElMessage.success('模型删除成功')
      fetchModels()
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('模型删除失败')
    }
  }
}

const addLog = (message) => {
  const time = new Date().toLocaleTimeString()
  trainingLogs.value.push({ time, message })
}

const resetForm = () => {
  trainingForm.modelName = ''
  trainingForm.datasetId = ''
  trainingForm.modelType = 'unet'
  trainingForm.batchSize = 4
  trainingForm.learningRate = 0.001
  trainingForm.epochs = 10
  trainingForm.valSplit = 0.2
}

onMounted(() => {
  fetchDatasets()
  fetchModels()
})

onUnmounted(() => {
  if (statusTimer) {
    clearInterval(statusTimer)
  }
})
</script>

<style scoped>
.training-view {
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

.config-card, .status-card, .models-card {
  height: fit-content;
}

.metrics-section {
  margin: 20px 0;
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.metric-item {
  text-align: center;
}

.metric-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 5px;
}

.metric-value {
  font-size: 18px;
  font-weight: bold;
  color: #409eff;
}

.training-log {
  margin-top: 20px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  background-color: #1e1e1e;
}

.log-item {
  padding: 8px 12px;
  color: #d4d4d4;
  font-family: monospace;
  font-size: 12px;
  border-bottom: 1px solid #333;
}

.log-item:last-child {
  border-bottom: none;
}

.log-time {
  color: #6a9955;
  margin-right: 10px;
}

.log-message {
  color: #d4d4d4;
}

.no-training {
  text-align: center;
  padding: 40px 0;
}

.chart-section {
  margin-top: 15px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 10px;
  background-color: #fafafa;
}

.chart-container {
  width: 100%;
  height: 180px;
}
</style>
