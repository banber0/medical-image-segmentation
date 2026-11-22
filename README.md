<div align="center">

# 医学影像分割平台

**Medical Image Segmentation Platform**

基于 ResNet34-UNet 的医学影像二值分割课程项目，集数据管理、模型训练、影像分割与效果评估于一体。

![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11-3776AB?logo=python&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-2.4.1-EE4C2C?logo=pytorch&logoColor=white)
![Vue](https://img.shields.io/badge/Vue-3-4FC08D?logo=vuedotjs&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-000000?logo=flask&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-8-4479A1?logo=mysql&logoColor=white)

[功能概览](#功能概览) · [系统架构](#系统架构) · [快速开始](#快速开始) · [数据集格式](#数据集格式) · [模型与训练](#模型与训练) · [架构图原文件](docs/architecture/README.md)

</div>

## 项目简介

本项目采用前后端分离设计：Vue 提供操作界面，Flask 提供业务 API，PyTorch 完成模型训练与推理。MySQL 保存用户、数据集、模型和操作记录，文件系统保存图像、标注、模型权重及分割结果。

主要面向心脏影像等二维灰度图像的前景 / 背景分割，模型输入为 `1 × 256 × 256`，输出为二值掩膜。可通过网页完成“上传数据集 → 训练模型 → 上传图像 → 查看分割 → 评估指标”的完整操作流程。

## 功能概览

| 模块 | 已实现功能 |
| --- | --- |
| 用户与个人信息 | 注册、登录、资料编辑、密码修改 |
| 数据集管理 | 上传 ZIP 并自动解压，查看文件列表，编辑与删除记录 |
| 模型训练 | 配置训练轮数、批次大小和学习率，后台线程训练，轮询查看进度，停止训练 |
| 训练可视化 | 展示训练 / 验证 Loss 与 Dice 曲线，保存训练历史及 Excel 报告 |
| 影像分割 | 选择模型、上传图像、生成掩膜、对比原图与分割结果 |
| 模型评估 | 上传测试图像和对应标签，计算 Accuracy、Precision、Recall、F1、IoU 与 Dice |
| 模型导入 | 上传与当前 ResNet34-UNet 结构一致的 PyTorch 权重 |
| 历史与反馈 | 查看训练、分割和评估历史，提交模型使用反馈 |
| 管理后台 | 用户管理与系统操作日志 |

## 系统架构

![系统逻辑架构](docs/architecture/逻辑架构图.png)

| 层级 | 技术与职责 |
| --- | --- |
| 展示层 | Vue 3、Vue Router、Element Plus、ECharts、Axios；负责交互、图像展示和指标可视化 |
| 业务层 | Flask、Flask-SQLAlchemy；负责用户、数据集、模型、训练任务与历史记录 API |
| 算法层 | PyTorch、segmentation-models-pytorch；负责预处理、ResNet34-UNet、训练和推理 |
| 存储层 | MySQL 保存结构化信息；本地目录保存数据集、权重与图像文件 |

### 算法结构示意

![分割算法结构示意](docs/architecture/算法图.png)

图中展示 U-Net 编码、解码及跳跃连接的总体思路；实际训练与推理使用 `segmentation_models_pytorch.Unet`，编码器为 ResNet34。`models/unet_model.py` 中另保留了独立 U-Net 定义。

### 设计文档

六张图均提供 **PNG 预览、SVG 导出和可编辑的 Visio `.vsdx` 原文件**，可在[架构图目录](docs/architecture/README.md)集中查看。

| 图纸 | 在线预览 |
| --- | --- | --- |
| 逻辑架构图 | [PNG](docs/architecture/逻辑架构图.png) |
| 系统物理架构图 | [PNG](docs/architecture/系统物理架构图.png) |
| 数据物理存储结构示意图 | [PNG](docs/architecture/数据物理存储结构示意图.png) |
| 算法图 | [PNG](docs/architecture/算法图.png) |
| 推理流程图 | [PNG](docs/architecture/推理流程图.png) ||
| 影像分割业务流程图 | [PNG](docs/architecture/影像分割业务流程图.png) |

架构图描述设计层面的模块关系。当前代码通过 Pillow 读取常见二维图像；图纸中涉及的 DICOM 等格式需先转换为 PNG 等图像后使用。

## 目录结构

```text
medical-image-segmentation/
├── app.py                        # Flask API、数据库模型和任务调度
├── requirements.txt              # 后端与算法依赖
├── .env.example                  # 后端配置示例
├── models/
│   ├── train.py                  # 数据加载、增强、训练与训练报告
│   ├── inference.py              # 模型加载、预处理、推理与掩膜输出
│   └── unet_model.py             # 独立 U-Net 定义
├── medical-platform/
│   ├── src/
│   │   ├── api/index.js          # API 请求封装
│   │   ├── router/index.js       # 前端路由
│   │   └── views/                # 登录、数据集、训练、分割等页面
│   ├── public/                   # 公共静态资源
│   ├── .env.example              # API 地址配置示例
│   ├── package.json
│   └── package-lock.json
└── docs/architecture/            # 六张设计图：VSDX、PNG、SVG
```

运行时会创建 `datasets/`、`uploads/` 和 `models/weights/`。数据集、上传文件、用户数据库、依赖安装目录和训练权重未提交到仓库，原始本地文件仍保留。

## 快速开始

### 1. 环境准备

| 环境 | 要求 |
| --- | --- |
| Python | 推荐 3.10 或 3.11 |
| Node.js | 推荐 22.12+；Vite 8 也支持 20.19+ |
| 数据库 | MySQL 8.0，需提前启动 |
| 计算设备 | 支持 CPU；有兼容的 NVIDIA CUDA 环境时自动使用 GPU |

```bash
git clone https://github.com/banber0/medical-image-segmentation.git
cd medical-image-segmentation
python -m venv .venv
```

Windows PowerShell 激活环境：

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS / Linux 激活环境：

```bash
source .venv/bin/activate
```

安装依赖：

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

依赖中已将 `torch==2.4.1` 与 `torchvision==0.19.1` 配对。如需指定 CPU 或 CUDA 版本，可先按 [PyTorch 官方历史版本说明](https://pytorch.org/get-started/previous-versions/#v241)安装对应二进制包，再安装本项目依赖。

### 2. 准备 MySQL

使用数据库管理员账号执行以下示例，并自行更换密码：

```sql
CREATE DATABASE IF NOT EXISTS medical_db
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'medical_user'@'127.0.0.1'
  IDENTIFIED BY 'replace_with_your_password';
GRANT ALL PRIVILEGES ON medical_db.* TO 'medical_user'@'127.0.0.1';
```

将根目录 `.env.example` 复制为 `.env`，设置实际连接信息：

```dotenv
DATABASE_URL=mysql+pymysql://medical_user:replace_with_your_password@127.0.0.1:3306/medical_db?charset=utf8mb4
HOST=127.0.0.1
PORT=5000
FLASK_DEBUG=0
```

密码含 `@`、`:`、`/` 等特殊字符时，需要进行 URL 编码。`.env` 已加入忽略列表。

### 3. 启动后端

在项目根目录执行：

```bash
python app.py
```

后端默认监听 `http://127.0.0.1:5000`，首次启动会在已有数据库中创建业务表。请始终从项目根目录启动，文件存储路径以当前工作目录为基准。

### 4. 启动前端

另开一个终端：

```bash
cd medical-platform
npm ci
npm run dev
```

打开终端显示的地址，通常为 `http://localhost:5173`。如果后端地址变化，将 `medical-platform/.env.example` 复制为 `.env`，修改 `VITE_API_BASE_URL` 后重启前端。

前端构建与本地预览：

```bash
npm run build
npm run preview
```

## 使用流程

1. 注册账号并登录平台。
2. 在“数据集”页面上传符合下述格式的 ZIP 压缩包。
3. 在“模型训练”中选择数据集，设置参数并开始训练；可查看 Loss / Dice 变化。
4. 训练完成后，在“影像分割”中选择已有权重的模型并上传图像。
5. 在模型测试页面上传测试图像和对应标签，查看分割指标。
6. 在历史记录中查看训练、分割与评估结果，或提交模型反馈。

也可通过“模型上传”导入现成权重。推理代码按 ResNet34-UNet 的 `state_dict` 加载模型，建议使用本项目训练得到的 `.pth` 文件；上传接口接受的其他扩展名不代表已实现对应推理引擎。

## 数据集格式

推荐 ZIP 解压后直接得到以下结构，以同时兼容训练和文件列表查看：

```text
dataset.zip
├── images/
│   ├── slice_001.png
│   ├── slice_002.png
│   └── ...
└── masks/
    ├── slice_001.png
    ├── slice_002.png
    └── ...
```

- 图像支持 `.png`、`.jpg`、`.jpeg`、`.bmp`、`.tif`、`.tiff`，训练时转为灰度图并缩放到 `256 × 256`。
- 对于 `slice_001.jpg`，训练程序依次查找 `slice_001.png`、`slice_001_mask.png`、`slice_001_label.png` 作为标签。
- 建议标签统一为背景 `0`、前景 `255` 的二值 PNG，以兼容训练和网页评估的阈值处理。
- 训练程序可以递归查找嵌套的 `images/` 与 `masks/`，但网页文件列表按数据集根目录读取，因此推荐以上布局。
- `drop_last=True` 会丢弃不足一个批次的训练数据，训练集图片数量至少应达到设置的 Batch Size。

上传的数据实际存放在 `datasets/<UUID>_<文件名>/`，数据库保存相应路径。需要清理时优先使用网页的数据集删除功能，同时清理文件和记录。

## 模型与训练

| 项目 | 实现 |
| --- | --- |
| 网络 | ResNet34 编码器 + U-Net 解码器，单通道输入、单通道 logits 输出 |
| 编码器初始化 | 训练使用 ImageNet 预训练权重，首次训练可能需要联网下载 |
| 损失函数 | `0.6 × Focal Loss + 0.4 × Dice Loss`，Focal `α=0.9`、`γ=2.0` |
| 优化器 | AdamW，`weight_decay=1e-4` |
| 学习率调度 | ReduceLROnPlateau，监控验证 Dice，`patience=3`、`factor=0.5` |
| 梯度处理 | 梯度范数裁剪，`max_norm=1.0` |
| 数据增强 | 同步水平 / 垂直翻转、±10° 旋转、轻微亮度与对比度变化 |
| 数据划分 | 随机种子 42，按图像文件划分为 70% 训练、10% 验证、20% 测试 |
| 最佳模型 | 按验证 Dice 保存 `best_model.pth`，另保存 `final_model.pth` |
| 训练产物 | 权重、配置、训练历史、测试结果与 `training_metrics.xlsx` |

页面初始参数为 Epochs `10`、Batch Size `4`、Learning Rate `0.001`；直接调用训练函数时，缺省值分别为 `30`、`4`、`0.0001`。`val_split` 参数目前不参与比例计算，实际划分以代码中的 `70/10/20` 为准。

若同一病例包含多张相邻切片，正式比较模型时应额外按病例划分数据，避免同一病例进入不同集合。

### 推理流程

```text
上传图像 → 灰度转换 → Resize(256×256) → ToTensor
         → ResNet34-UNet → Sigmoid → 概率 > 0.5
         → 0/255 二值掩膜 → 保存 PNG、记录历史、返回 Base64
```

当前推理输出为 `256 × 256`，不会自动恢复到原始图像尺寸。

## API 与数据存储

| 接口组 | 代表接口 |
| --- | --- |
| 用户 | `POST /api/register`、`POST /api/login`、`GET/POST /api/user/profile` |
| 数据集 | `GET/POST /api/datasets`、`GET/PUT/DELETE /api/datasets/<id>` |
| 模型 | `GET/POST /api/models`、`POST /api/models/upload` |
| 训练 | `POST /api/models/train`、`GET /api/models/train/status/<id>`、`POST /api/models/train/stop/<id>` |
| 推理与评估 | `POST /api/segmentation`、`POST /api/models/evaluate` |
| 历史 | `GET /api/history/training`、`GET /api/history/segmentation`、`GET /api/history/evaluation` |
| 反馈 | `GET/POST /api/feedbacks` |
| 管理 | `/api/admin/users`、`GET /api/admin/logs` |

MySQL 业务表包括 `users`、`datasets`、`models`、`training_history`、`evaluations`、`segmentation_history`、`feedbacks` 和 `system_logs`。大体积文件保存在磁盘，数据库中只记录文件路径与业务属性。

## 常见问题

**为什么仓库里没有数据集和训练权重？**

这些文件需要单独准备。仓库通过 `.gitignore` 排除了原始数据、上传内容、训练产物和本地数据库；克隆后可上传自己的数据集重新训练，或导入兼容权重。

**后端启动时提示数据库连接失败？**

检查 MySQL 是否启动、`medical_db` 是否已创建、`.env` 中用户名和密码是否正确，以及数据库账号是否允许从 `127.0.0.1` 连接。

**训练提示缺少目录或标签？**

确认 ZIP 中有 `images/` 与 `masks/`，每张原图都具有匹配命名的 PNG 标签。原始三维医学影像文件需要先完成切片与格式转换。

**没有 GPU 能否运行？**

可以，代码自动回退到 CPU；训练速度取决于硬件和数据规模。

## 项目范围

本仓库用于课程学习与本地演示。当前实现中的角色展示、前端路由和用户 ID 参数并不构成完整的服务端权限控制；CORS 也采用开发配置。若需要部署到公共网络，应先完善认证授权、上传校验与任务管理。系统结果用于算法演示。

## 相关项目

- [PyTorch](https://pytorch.org/)
- [segmentation-models-pytorch](https://github.com/qubvel-org/segmentation_models.pytorch)
- [Flask](https://flask.palletsprojects.com/)
- [Vue](https://vuejs.org/)
- [Element Plus](https://element-plus.org/)
- [Vite](https://vite.dev/guide/)
