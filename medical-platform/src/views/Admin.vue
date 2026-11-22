<template>
  <div class="admin-view">
    <div class="header">
      <h2>系统管理</h2>
    </div>

    <el-card class="admin-card">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="用户管理" name="users">
          <div class="admin-header">
            <el-button type="primary" @click="showAddUserDialog = true">
              <el-icon><Plus /></el-icon>
              添加用户
            </el-button>
          </div>
          <el-table :data="users" v-loading="loadingUsers" style="width: 100%">
            <el-table-column prop="id" label="ID" width="60"></el-table-column>
            <el-table-column prop="username" label="用户名" min-width="120"></el-table-column>
            <el-table-column prop="email" label="邮箱" min-width="180"></el-table-column>
            <el-table-column prop="userType" label="用户类型" width="100">
              <template #default="scope">
                <el-tag :type="scope.row.userType === 'admin' ? 'danger' : 'success'">
                  {{ scope.row.userType === 'admin' ? '管理员' : '普通用户' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" width="160"></el-table-column>
            <el-table-column label="操作" width="150">
              <template #default="scope">
                <el-button size="small" @click="editUser(scope.row)">编辑</el-button>
                <el-button size="small" type="danger" @click="deleteUser(scope.row.id)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="系统日志" name="logs">
          <el-table :data="logs" v-loading="loadingLogs" style="width: 100%">
            <el-table-column prop="id" label="ID" width="60"></el-table-column>
            <el-table-column prop="user" label="用户" min-width="120"></el-table-column>
            <el-table-column prop="action" label="操作" min-width="150"></el-table-column>
            <el-table-column prop="description" label="描述" min-width="200"></el-table-column>
            <el-table-column prop="created_at" label="操作时间" width="160"></el-table-column>
          </el-table>
          <el-empty v-if="!loadingLogs && logs.length === 0" description="暂无日志"></el-empty>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 添加用户对话框 -->
    <el-dialog v-model="showAddUserDialog" title="添加用户" width="450px">
      <el-form :model="userForm" :rules="userRules" ref="userFormRef" label-width="80px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="userForm.username" placeholder="请输入用户名"></el-input>
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="userForm.password" type="password" show-password placeholder="请输入密码"></el-input>
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="userForm.email" placeholder="请输入邮箱"></el-input>
        </el-form-item>
        <el-form-item label="用户类型" prop="userType">
          <el-select v-model="userForm.userType" style="width: 100%;">
            <el-option label="普通用户" value="user"></el-option>
            <el-option label="管理员" value="admin"></el-option>
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddUserDialog = false">取消</el-button>
        <el-button type="primary" @click="addUser">添加</el-button>
      </template>
    </el-dialog>

    <!-- 编辑用户对话框 -->
    <el-dialog v-model="showEditUserDialog" title="编辑用户" width="450px">
      <el-form :model="editUserForm" label-width="80px">
        <el-form-item label="用户名">
          <el-input v-model="editUserForm.username" disabled></el-input>
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="editUserForm.email" placeholder="请输入邮箱"></el-input>
        </el-form-item>
        <el-form-item label="用户类型">
          <el-select v-model="editUserForm.userType" style="width: 100%;">
            <el-option label="普通用户" value="user"></el-option>
            <el-option label="管理员" value="admin"></el-option>
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditUserDialog = false">取消</el-button>
        <el-button type="primary" @click="updateUser">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { adminAPI } from '../api/index'

const activeTab = ref('users')

const users = ref([])
const logs = ref([])
const loadingUsers = ref(false)
const loadingLogs = ref(false)

const showAddUserDialog = ref(false)
const showEditUserDialog = ref(false)

const userFormRef = ref(null)

const userForm = reactive({
  username: '',
  password: '',
  email: '',
  userType: 'user'
})

const editUserForm = reactive({
  id: '',
  username: '',
  email: '',
  userType: 'user'
})

const userRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }, { min: 6, message: '密码至少6位', trigger: 'blur' }]
}

const fetchUsers = async () => {
  loadingUsers.value = true
  try {
    const res = await adminAPI.getUsers()
    if (res.success) {
      users.value = res.users
    }
  } catch (error) {
    ElMessage.error('获取用户列表失败')
  } finally {
    loadingUsers.value = false
  }
}

const fetchLogs = async () => {
  loadingLogs.value = true
  try {
    const res = await adminAPI.getLogs()
    if (res.success) {
      logs.value = res.logs
    }
  } catch (error) {
    ElMessage.error('获取系统日志失败')
  } finally {
    loadingLogs.value = false
  }
}

const addUser = async () => {
  if (!userForm.username || !userForm.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }

  try {
    const res = await adminAPI.addUser(userForm)
    if (res.success) {
      ElMessage.success('用户添加成功')
      showAddUserDialog.value = false
      userForm.username = ''
      userForm.password = ''
      userForm.email = ''
      userForm.userType = 'user'
      fetchUsers()
    }
  } catch (error) {
    ElMessage.error('用户添加失败')
  }
}

const editUser = (row) => {
  editUserForm.id = row.id
  editUserForm.username = row.username
  editUserForm.email = row.email
  editUserForm.userType = row.userType
  showEditUserDialog.value = true
}

const updateUser = async () => {
  try {
    const res = await adminAPI.updateUser(editUserForm.id, {
      email: editUserForm.email,
      userType: editUserForm.userType
    })
    if (res.success) {
      ElMessage.success('用户编辑成功')
      showEditUserDialog.value = false
      fetchUsers()
    }
  } catch (error) {
    ElMessage.error('用户编辑失败')
  }
}

const deleteUser = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除该用户吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    const res = await adminAPI.deleteUser(id)
    if (res.success) {
      ElMessage.success('用户删除成功')
      fetchUsers()
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('用户删除失败')
    }
  }
}

onMounted(() => {
  fetchUsers()
  fetchLogs()
})
</script>

<style scoped>
.admin-view {
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

.admin-card {
  margin-top: 20px;
}

.admin-header {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 20px;
}
</style>
