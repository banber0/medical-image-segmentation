import axios from 'axios';

// 创建axios实例
const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api',
  timeout: 60000
});

// 请求拦截器
service.interceptors.request.use(
  config => {
    // 可以添加token
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  error => {
    return Promise.reject(error);
  }
);

// 响应拦截器
service.interceptors.response.use(
  response => {
    return response.data;
  },
  error => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

// ================= 用户接口 =================
export const userAPI = {
  // 注册
  register: (data) => service.post('/register', data),
  // 登录
  login: (data) => service.post('/login', data),
  // 获取用户信息
  getProfile: (username) => service.get(`/user/profile?username=${username}`),
  // 更新用户信息
  updateProfile: (data) => service.post(`/user/profile?username=${data.username}`, data),
  // 修改密码
  changePassword: (username, data) => service.post(`/user/change-password?username=${username}`, data)
};

// ================= 数据集接口 =================
export const datasetAPI = {
  // 获取数据集列表
  getList: (userId) => service.get(`/datasets?user_id=${userId || ''}`),
  // 上传数据集
  upload: (formData) => service.post('/datasets', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  // 获取数据集详情
  getDetail: (id) => service.get(`/datasets/${id}`),
  // 更新数据集
  update: (id, data) => service.put(`/datasets/${id}`, data),
  // 删除数据集
  delete: (id) => service.delete(`/datasets/${id}`),
  // 获取数据集文件
  getFiles: (id) => service.get(`/datasets/${id}/files`)
};

// ================= 模型接口 =================
export const modelAPI = {
  // 获取模型列表
  getList: (userId) => service.get(`/models?user_id=${userId || ''}`),
  // 创建模型
  create: (data) => service.post('/models', data),
  // 获取模型详情
  getDetail: (id) => service.get(`/models/${id}`),
  // 删除模型
  delete: (id) => service.delete(`/models/${id}`),
  // 训练模型
  train: (data) => service.post('/models/train', data),
  // 获取训练状态
  getTrainingStatus: (trainingId) => service.get(`/models/train/status/${trainingId}`),
  // 停止训练
  stopTraining: (trainingId) => service.post(`/models/train/stop/${trainingId}`)
};

// ================= 评估接口 =================
export const evaluateAPI = {
  // 评估模型
  evaluate: (formData) => service.post('/models/evaluate', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  // 获取评估历史
  getHistory: (userId) => service.get(`/history/evaluation?user_id=${userId || ''}`)
};

// ================= 分割接口 =================
export const segmentationAPI = {
  // 执行分割
  segment: (formData) => service.post('/segmentation', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  // 获取分割历史
  getHistory: (userId) => service.get(`/history/segmentation?user_id=${userId || ''}`),
  // 获取分割历史详情
  getHistoryDetail: (id) => service.get(`/history/segmentation/${id}`)
};

// ================= 反馈接口 =================
export const feedbackAPI = {
  // 获取反馈列表
  getList: (userId) => service.get(`/feedbacks?user_id=${userId || ''}`),
  // 提交反馈
  submit: (data) => service.post('/feedbacks', data)
};

// ================= 训练历史接口 =================
export const trainingAPI = {
  getHistory: (userId) => service.get(`/history/training?user_id=${userId || ''}`)
};

// ================= 管理员接口 =================
export const adminAPI = {
  // 获取用户列表
  getUsers: () => service.get('/admin/users'),
  // 添加用户
  addUser: (data) => service.post('/admin/users', data),
  // 更新用户
  updateUser: (id, data) => service.put(`/admin/users/${id}`, data),
  // 删除用户
  deleteUser: (id) => service.delete(`/admin/users/${id}`),
  // 获取日志
  getLogs: () => service.get('/admin/logs')
};

export default service;
