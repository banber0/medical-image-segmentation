<template>
  <div class="datasets-view">
    <div class="header">
      <h2>数据集管理</h2>
      <el-button type="primary" @click="showUploadDialog = true">
        <el-icon><Upload /></el-icon>
        上传数据集
      </el-button>
    </div>

    <el-card class="datasets-card">
      <el-table :data="datasets" v-loading="loading" style="width: 100%">
        <el-table-column prop="id" label="ID" width="60"></el-table-column>
        <el-table-column prop="name" label="数据集名称" min-width="150"></el-table-column>
        <el-table-column prop="description" label="描述" min-width="200"></el-table-column>
        <el-table-column prop="type" label="类型" width="100">
          <template #default="scope">
            <el-tag :type="getTypeTag(scope.row.type)">{{ getTypeText(scope.row.type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="size" label="大小" width="100"></el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160"></el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="scope">
            <el-button size="small" @click="editDataset(scope.row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteDataset(scope.row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!loading && datasets.length === 0" description="暂无数据集，请上传"></el-empty>
    </el-card>

    <!-- 上传数据集对话框 -->
    <el-dialog v-model="showUploadDialog" title="上传数据集" width="500px" :close-on-click-modal="false">
      <el-form :model="uploadForm" :rules="uploadRules" ref="uploadFormRef" label-width="100px">
        <el-form-item label="数据集名称" prop="name">
          <el-input v-model="uploadForm.name" placeholder="请输入数据集名称"></el-input>
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="uploadForm.description" type="textarea" :rows="3" placeholder="请输入数据集描述"></el-input>
        </el-form-item>
        <el-form-item label="类型" prop="type">
          <el-select v-model="uploadForm.type" style="width: 100%;">
            <el-option label="肝脏" value="liver"></el-option>
            <el-option label="病理细胞" value="cell"></el-option>
            <el-option label="肿瘤" value="tumor"></el-option>
            <el-option label="其他" value="other"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="数据集文件" prop="file">
          <el-upload
            class="upload-dataset"
            ref="uploadRef"
            action="#"
            :auto-upload="false"
            :on-change="handleFileChange"
            :limit="1"
            :http-request="customUpload"
            drag
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">
              将文件拖到此处，或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                支持 zip、rar 格式的压缩文件，内部需包含 images 和 masks 文件夹
              </div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showUploadDialog = false">取消</el-button>
          <el-button type="primary" @click="uploadDataset" :loading="uploading">上传</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 编辑数据集对话框 -->
    <el-dialog v-model="showEditDialog" title="编辑数据集" width="500px">
      <el-form :model="editForm" :rules="editRules" ref="editFormRef" label-width="100px">
        <el-form-item label="数据集名称" prop="name">
          <el-input v-model="editForm.name"></el-input>
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="editForm.description" type="textarea" :rows="3"></el-input>
        </el-form-item>
        <el-form-item label="类型" prop="type">
          <el-select v-model="editForm.type" style="width: 100%;">
            <el-option label="肝脏" value="liver"></el-option>
            <el-option label="病理细胞" value="cell"></el-option>
            <el-option label="肿瘤" value="tumor"></el-option>
            <el-option label="其他" value="other"></el-option>
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showEditDialog = false">取消</el-button>
          <el-button type="primary" @click="saveDataset">保存</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload, UploadFilled } from '@element-plus/icons-vue'
import { datasetAPI } from '../api/index'

const datasets = ref([])
const loading = ref(false)
const showUploadDialog = ref(false)
const showEditDialog = ref(false)
const uploading = ref(false)
const uploadFormRef = ref(null)
const editFormRef = ref(null)
const uploadRef = ref(null)

const userInfo = computed(() => {
  const user = localStorage.getItem('user')
  return user ? JSON.parse(user) : null
})

const uploadForm = reactive({
  name: '',
  description: '',
  type: 'liver',
  file: null
})

const editForm = reactive({
  id: '',
  name: '',
  description: '',
  type: ''
})

const uploadRules = {
  name: [{ required: true, message: '请输入数据集名称', trigger: 'blur' }],
  type: [{ required: true, message: '请选择数据集类型', trigger: 'change' }],
  file: [{ required: true, message: '请上传数据集文件', trigger: 'change' }]
}

const editRules = {
  name: [{ required: true, message: '请输入数据集名称', trigger: 'blur' }],
  type: [{ required: true, message: '请选择数据集类型', trigger: 'change' }]
}

const getTypeText = (type) => {
  const types = { liver: '肝脏', cell: '病理细胞', tumor: '肿瘤', other: '其他' }
  return types[type] || type
}

const getTypeTag = (type) => {
  const tags = { liver: 'primary', cell: 'success', tumor: 'warning', other: 'info' }
  return tags[type] || 'info'
}

const fetchDatasets = async () => {
  loading.value = true
  try {
    const res = await datasetAPI.getList(userInfo.value?.user_id)
    if (res.success) {
      datasets.value = res.datasets
    }
  } catch (error) {
    ElMessage.error('获取数据集列表失败')
  } finally {
    loading.value = false
  }
}

const handleFileChange = (file) => {
  uploadForm.file = file.raw
}

const customUpload = () => {
  // 自定义上传，由submitDataset处理
}

const uploadDataset = async () => {
  if (!uploadForm.file) {
    ElMessage.warning('请选择数据集文件')
    return
  }

  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('name', uploadForm.name)
    formData.append('description', uploadForm.description)
    formData.append('type', uploadForm.type)
    formData.append('user_id', userInfo.value?.user_id)
    formData.append('file', uploadForm.file)

    const res = await datasetAPI.upload(formData)
    if (res.success) {
      ElMessage.success('数据集上传成功')
      showUploadDialog.value = false
      uploadForm.name = ''
      uploadForm.description = ''
      uploadForm.type = 'liver'
      uploadForm.file = null
      fetchDatasets()
    }
  } catch (error) {
    ElMessage.error(error.message || '数据集上传失败')
  } finally {
    uploading.value = false
  }
}

const editDataset = (row) => {
  editForm.id = row.id
  editForm.name = row.name
  editForm.description = row.description
  editForm.type = row.type
  showEditDialog.value = true
}

const saveDataset = async () => {
  try {
    const res = await datasetAPI.update(editForm.id, editForm)
    if (res.success) {
      ElMessage.success('数据集编辑成功')
      showEditDialog.value = false
      fetchDatasets()
    }
  } catch (error) {
    ElMessage.error('数据集编辑失败')
  }
}

const deleteDataset = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除该数据集吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    const res = await datasetAPI.delete(id)
    if (res.success) {
      ElMessage.success('数据集删除成功')
      fetchDatasets()
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('数据集删除失败')
    }
  }
}

onMounted(() => {
  fetchDatasets()
})
</script>

<style scoped>
.datasets-view {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header h2 {
  margin: 0;
  font-size: 20px;
  color: #303133;
}

.datasets-card {
  margin-top: 20px;
}

.upload-dataset {
  width: 100%;
}
</style>
