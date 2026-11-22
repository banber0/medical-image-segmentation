<template>
  <div class="feedback-view">
    <div class="header">
      <h2>模型反馈</h2>
    </div>

    <el-card class="feedback-card">
      <el-table :data="feedbacks" v-loading="loading" style="width: 100%">
        <el-table-column prop="id" label="ID" width="60"></el-table-column>
        <el-table-column prop="modelName" label="模型名称" min-width="150"></el-table-column>
        <el-table-column prop="feedback" label="反馈内容" min-width="200"></el-table-column>
        <el-table-column prop="score" label="评分" width="150">
          <template #default="scope">
            <el-rate v-model="scope.row.score" disabled show-score></el-rate>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="反馈时间" width="160"></el-table-column>
      </el-table>

      <el-empty v-if="!loading && feedbacks.length === 0" description="暂无反馈记录"></el-empty>
    </el-card>

    <!-- 查看反馈对话框 -->
    <el-dialog v-model="showDialog" title="反馈详情" width="500px">
      <el-descriptions :column="1" border>
        <el-descriptions-item label="模型名称">{{ selectedFeedback.modelName }}</el-descriptions-item>
        <el-descriptions-item label="反馈内容">{{ selectedFeedback.feedback }}</el-descriptions-item>
        <el-descriptions-item label="评分">
          <el-rate v-model="selectedFeedback.score" disabled show-score></el-rate>
        </el-descriptions-item>
        <el-descriptions-item label="反馈时间">{{ selectedFeedback.created_at }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { feedbackAPI } from '../api/index'

const feedbacks = ref([])
const loading = ref(false)
const showDialog = ref(false)

const userInfo = computed(() => {
  const user = localStorage.getItem('user')
  return user ? JSON.parse(user) : null
})

const selectedFeedback = reactive({
  modelName: '',
  feedback: '',
  score: 0,
  created_at: ''
})

const fetchFeedbacks = async () => {
  loading.value = true
  try {
    // 获取当前用户的反馈，如果 userInfo 为 null 则获取所有
    const res = await feedbackAPI.getList(userInfo.value?.user_id || '')
    if (res.success) {
      feedbacks.value = res.feedbacks || []
      console.log('反馈数据:', feedbacks.value)
    }
  } catch (error) {
    ElMessage.error('获取反馈列表失败')
  } finally {
    loading.value = false
  }
}

const viewFeedback = (row) => {
  selectedFeedback.modelName = row.modelName
  selectedFeedback.feedback = row.feedback
  selectedFeedback.score = row.score
  selectedFeedback.created_at = row.created_at
  showDialog.value = true
}

onMounted(() => {
  fetchFeedbacks()
})
</script>

<style scoped>
.feedback-view {
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

.feedback-card {
  margin-top: 20px;
}
</style>
