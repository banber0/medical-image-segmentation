# 医学影像分割平台 · 前端

Vue 3 + Vue Router + Element Plus + ECharts，使用 Vite 构建。

完整安装步骤、架构图、后端配置与数据集说明见[项目 README](../README.md)。

需要 Node.js 22.12+（或 20.19+）：

```bash
npm ci
npm run dev
```

默认后端地址为 `http://localhost:5000/api`。如需修改，将 `.env.example` 复制为 `.env`，设置 `VITE_API_BASE_URL`，然后重启开发服务器。

```bash
npm run build
npm run preview
```

`build` 输出到 `dist/`；`preview` 用于本地检查构建结果。
