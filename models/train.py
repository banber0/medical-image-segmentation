"""
Unet模型训练服务
提供训练接口
"""
import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import torchvision.transforms.functional as TF
from PIL import Image
import numpy as np
import json
from datetime import datetime
import shutil
import glob
import random
import openpyxl
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill

# ================= 引入预训练模型库 =================
import segmentation_models_pytorch as smp
# ====================================================

# 设备配置
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"训练设备: {device}")

# 训练停止标志（字典支持跨线程访问）
_stop_flags = {}

def stop_training(training_id):
    """标记训练任务停止"""
    _stop_flags[training_id] = True

def is_training_stopped(training_id):
    """检查训练是否被请求停止"""
    return _stop_flags.get(training_id, False)

def clear_stop_flag(training_id):
    """清除停止标志"""
    if training_id in _stop_flags:
        del _stop_flags[training_id]


# ---------------- 同步数据增强 ----------------
class JointTransform:
    """医学灰度图像和Mask同步进行数据增强的转换器"""
    def __init__(self, is_train=True):
        self.is_train = is_train

    def __call__(self, image, mask):
        # 统一缩放 (Image.BILINEAR 用于图像, Image.NEAREST 用于Mask以保持0/1边缘)
        image = TF.resize(image, (256, 256), interpolation=Image.BILINEAR)
        mask = TF.resize(mask, (256, 256), interpolation=Image.NEAREST)

        if self.is_train:
            # 1. 空间变换保留
            if random.random() > 0.5:
                image = TF.hflip(image)
                mask = TF.hflip(mask)

            if random.random() > 0.5:
                image = TF.vflip(image)
                mask = TF.vflip(mask)

            # 旋转角度减小到 -10 到 10 度
            angle = random.uniform(-10, 10)
            image = TF.rotate(image, angle, interpolation=Image.BILINEAR)
            mask = TF.rotate(mask, angle, interpolation=Image.NEAREST)

            # 2. 亮度/对比度微调的幅度大大减小
            if random.random() > 0.5:
                brightness_factor = random.uniform(0.95, 1.05)
                image = TF.adjust_brightness(image, brightness_factor)
                contrast_factor = random.uniform(0.95, 1.05)
                image = TF.adjust_contrast(image, contrast_factor)

        # 转换为张量 (自动将 0-255 缩放到 0.0-1.0)
        image = TF.to_tensor(image)
        mask = TF.to_tensor(mask)

        # 确保 mask 为严格的 0 或 1 二值图
        mask = (mask > 0).float()

        return image, mask


class MedicalDataset(Dataset):
    """医学影像数据集"""
    def __init__(self, image_paths, mask_dir, transform=None):
        self.images = image_paths
        self.mask_dir = mask_dir
        self.transform = transform

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):
        img_path = self.images[idx]

        # 获取对应的mask
        img_name = os.path.basename(img_path)
        name, ext = os.path.splitext(img_name)

        # -------- 🚨修复致命BUG：绝不能用原图当测试回退 --------
        possible_mask_names = [
            name + '.png',
            name + '_mask.png',
            name + '_label.png'
        ]

        mask_path = None
        for m_name in possible_mask_names:
            temp_path = os.path.join(self.mask_dir, m_name)
            if os.path.exists(temp_path):
                mask_path = temp_path
                break

        if mask_path is None:
            raise FileNotFoundError(f"\n[严重错误] 找不到图片 {img_name} 对应的 Mask 标签文件！\n"
                                    f"请检查:\n1. 标签文件是否放入了 masks 文件夹\n"
                                    f"2. 命名是否是 {name}.png 或 {name}_mask.png")
        # --------------------------------------------------------

        # 加载图像和mask
        image = Image.open(img_path).convert('L')
        mask = Image.open(mask_path).convert('L')

        # 应用联合数据增强
        if self.transform:
            image, mask = self.transform(image, mask)
        else:
            # Fallback
            image = TF.to_tensor(TF.resize(image, (256, 256)))
            mask = (TF.to_tensor(TF.resize(mask, (256, 256))) > 0).float()

        return image, mask


# ---------------- 全新替换：极度不平衡专用损失函数 ----------------
class FocalLoss(nn.Module):
    """针对极度不平衡数据的 Focal Loss，死磕小病灶"""
    def __init__(self, alpha=0.9, gamma=2.0):
        super(FocalLoss, self).__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.bce = nn.BCEWithLogitsLoss(reduction='none')

    def forward(self, inputs, targets):
        bce_loss = self.bce(inputs, targets)
        probs = torch.sigmoid(inputs)
        p_t = probs * targets + (1 - probs) * (1 - targets)
        alpha_t = self.alpha * targets + (1 - self.alpha) * (1 - targets)
        focal_loss = alpha_t * (1 - p_t) ** self.gamma * bce_loss
        return focal_loss.mean()

class DiceLoss(nn.Module):
    """平滑版 Dice Loss"""
    def __init__(self, smooth=1e-5):
        super(DiceLoss, self).__init__()
        self.smooth = smooth

    def forward(self, pred_logits, target):
        pred_probs = torch.sigmoid(pred_logits).view(-1)
        target = target.view(-1)
        intersection = (pred_probs * target).sum()
        dice = (2. * intersection + self.smooth) / (pred_probs.sum() + target.sum() + self.smooth)
        return 1 - dice

class CombinedLoss(nn.Module):
    """王炸组合：Focal Loss (找点) + Dice Loss (抓面)"""
    def __init__(self, focal_weight=0.6, dice_weight=0.4):
        super(CombinedLoss, self).__init__()
        self.focal = FocalLoss(alpha=0.9, gamma=2.0)
        self.dice = DiceLoss(smooth=1e-5)
        self.focal_weight = focal_weight
        self.dice_weight = dice_weight

    def forward(self, pred_logits, target):
        return self.focal_weight * self.focal(pred_logits, target) + self.dice_weight * self.dice(pred_logits, target)
# -----------------------------------------------------------------


def train_model(dataset_path, output_dir, config=None, training_id=None, progress_callback=None):
    if training_id is None:
        training_id = hash((dataset_path, output_dir, datetime.now().timestamp()))

    clear_stop_flag(training_id)
    if config is None:
        config = {}

    epochs = config.get('epochs', 30)
    batch_size = config.get('batch_size', 4)
    # 因为用了预训练模型，学习率推荐降低到 1e-4 防止破坏预训练权重
    learning_rate = config.get('learning_rate', 1e-4)
    val_split = config.get('val_split', 0.2)

    def find_dir(base_path, target):
        if os.path.exists(os.path.join(base_path, target)):
            return os.path.join(base_path, target)
        for item in os.listdir(base_path):
            item_path = os.path.join(base_path, item)
            if os.path.isdir(item_path):
                result = find_dir(item_path, target)
                if result:
                    return result
        return None

    images_dir = find_dir(dataset_path, 'images')
    masks_dir = find_dir(dataset_path, 'masks')

    if not images_dir or not masks_dir:
        return {'success': False, 'error': f'目录不完整: {dataset_path}'}

    all_images = sorted(glob.glob(os.path.join(images_dir, '*')))
    all_images = [f for f in all_images if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff'))]

    random.seed(42)
    shuffled_images = all_images.copy()
    random.shuffle(shuffled_images)

    total = len(shuffled_images)
    train_size = int(total * 0.7)          # 70% 训练集
    val_size = int(total * 0.1)            # 10% 验证集
    # 剩余 20% 作为测试集

    train_images = shuffled_images[:train_size]
    val_images = shuffled_images[train_size:train_size + val_size]
    test_images = shuffled_images[train_size + val_size:]  # 20% 测试集

    print(f"数据集划分: 训练集 {len(train_images)}张, 验证集 {len(val_images)}张, 测试集 {len(test_images)}张")

    train_dataset = MedicalDataset(train_images, masks_dir, transform=JointTransform(is_train=True))
    val_dataset = MedicalDataset(val_images, masks_dir, transform=JointTransform(is_train=False))
    test_dataset = MedicalDataset(test_images, masks_dir, transform=JointTransform(is_train=False))

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=0, drop_last=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=0)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, num_workers=0)

    # ---------------- 核心替换：预训练 ResNet34-UNet ----------------
    print("🚀 正在加载基于 ResNet34 的预训练 UNet 模型...")
    model = smp.Unet(
        encoder_name="resnet34",
        encoder_weights="imagenet",
        in_channels=1,
        classes=1,
        activation=None
    ).to(device)
    # ----------------------------------------------------------------

    criterion = CombinedLoss(focal_weight=0.6, dice_weight=0.4)
    optimizer = optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=1e-4)
    # 将调度器改为监控 Dice 指标 (越大越好, mode='max')
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='max', patience=3, factor=0.5, min_lr=1e-6)

    history = {'train_loss': [], 'val_loss': [], 'train_dice': [], 'val_dice': []}

    # 【非常关键】：对于不平衡数据，绝不能用Loss评判模型好坏，必须用Dice！
    best_val_dice = 0.0

    best_model_path = os.path.join(output_dir, 'best_model.pth')
    os.makedirs(output_dir, exist_ok=True)

    for epoch in range(epochs):
        if progress_callback:
            progress_callback(epoch + 1, epochs)
        if is_training_stopped(training_id):
            return {'success': False, 'output_dir': output_dir, 'error': 'Training stopped by user', 'stopped': True}

        model.train()
        train_loss, train_dice = 0.0, 0.0

        for batch_count, (images, masks) in enumerate(train_loader, 1):

            # -------- 数据探针检查 --------
            if epoch == 0 and batch_count == 1:
                print("\n" + "="*40 + " 数据探针检查 " + "="*40)
                print(f"图像 (Image) 最大值: {images.max().item():.4f}, 最小值: {images.min().item():.4f}")
                print(f"标签 (Mask)  最大值: {masks.max().item():.4f}, 最小值: {masks.min().item():.4f}")
                print(f"标签中包含病灶(白色像素)的比例: {masks.mean().item():.6f}")
                print("="*94 + "\n")
                if masks.max().item() == 0:
                    print("⚠️ [非常危险] 第一批次的 Mask 全是纯黑色的！请检查你的数据集标签是否正确！")

            images, masks = images.to(device), masks.to(device)

            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, masks)
            loss.backward()

            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()

            train_loss += loss.item()

            # 指标计算 (无需梯度)
            with torch.no_grad():
                pred = (torch.sigmoid(outputs) > 0.5).float()
                intersection = (pred * masks).sum()
                dice = (2. * intersection + 1e-5) / (pred.sum() + masks.sum() + 1e-5)

            train_dice += dice.item()
            print(f"  Batch {batch_count}/{len(train_loader)} - Loss: {loss.item():.4f}, Dice: {dice.item():.4f}", flush=True)

        train_loss /= len(train_loader)
        train_dice /= len(train_loader)

        # -------- 验证阶段 --------
        model.eval()
        val_loss, val_dice = 0.0, 0.0

        with torch.no_grad():
            for images, masks in val_loader:
                images, masks = images.to(device), masks.to(device)

                outputs = model(images)
                loss = criterion(outputs, masks)
                val_loss += loss.item()

                pred = (torch.sigmoid(outputs) > 0.5).float()
                intersection = (pred * masks).sum()
                dice = (2. * intersection + 1e-5) / (pred.sum() + masks.sum() + 1e-5)
                val_dice += dice.item()

        val_loss /= len(val_loader) if len(val_loader) > 0 else 1
        val_dice /= len(val_loader) if len(val_loader) > 0 else 1

        # 根据验证集的 Dice 指标来衰减学习率
        scheduler.step(val_dice)

        history['train_loss'].append(train_loss)
        history['val_loss'].append(val_loss)
        history['train_dice'].append(train_dice)
        history['val_dice'].append(val_dice)

        print(f"Epoch {epoch+1}/{epochs} - Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f} | Train Dice: {train_dice:.4f}, Val Dice: {val_dice:.4f}", flush=True)

        # 【修改保存逻辑】：以 Dice 为准！只要 Dice 上升就保存！
        if val_dice > best_val_dice:
            best_val_dice = val_dice
            torch.save(model.state_dict(), best_model_path)
            print(f"  🌟 发现更好的模型！验证集 Dice 提升至: {best_val_dice:.4f}，已保存")

    final_model_path = os.path.join(output_dir, 'final_model.pth')
    torch.save(model.state_dict(), final_model_path)

    # -------- 测试集评估 --------
    print("\n📊 正在测试集上评估最佳模型...")
    model.load_state_dict(torch.load(best_model_path))  # 加载最佳模型
    model.eval()
    test_loss, test_dice = 0.0, 0.0
    with torch.no_grad():
        for images, masks in test_loader:
            images, masks = images.to(device), masks.to(device)
            outputs = model(images)
            loss = criterion(outputs, masks)
            test_loss += loss.item()

            pred = (torch.sigmoid(outputs) > 0.5).float()
            intersection = (pred * masks).sum()
            dice = (2. * intersection + 1e-5) / (pred.sum() + masks.sum() + 1e-5)
            test_dice += dice.item()

    test_loss /= len(test_loader) if len(test_loader) > 0 else 1
    test_dice /= len(test_loader) if len(test_loader) > 0 else 1
    print(f"  测试集 Loss: {test_loss:.4f}, 测试集 Dice: {test_dice:.4f}")

    # 保存测试结果
    test_result = {'test_loss': test_loss, 'test_dice': test_dice}
    with open(os.path.join(output_dir, 'test_result.json'), 'w') as f:
        json.dump(test_result, f, indent=2)

    with open(os.path.join(output_dir, 'training_history.json'), 'w') as f:
        json.dump({k: [float(v) for v in vals] for k, vals in history.items()}, f, indent=2)
    with open(os.path.join(output_dir, 'config.json'), 'w') as f:
        json.dump(config, f, indent=2)

    # 生成 Excel 训练报告
    _generate_training_excel(output_dir, config, history, best_val_dice, test_dice)

    return {'success': True, 'output_dir': output_dir, 'best_model': best_model_path, 'final_model': final_model_path, 'history': history, 'final_val_dice': val_dice, 'test_dice': test_dice}


def _generate_training_excel(output_dir, config, history, best_val_dice, test_dice=None):
    """生成训练指标Excel报告"""
    excel_path = os.path.join(output_dir, 'training_metrics.xlsx')
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = '训练指标'

    # 样式定义
    header_font = Font(bold=True, size=12, color='FFFFFF')
    header_fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
    header_alignment = Alignment(horizontal='center', vertical='center')
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    # 设置列宽
    ws.column_dimensions['A'].width = 12
    ws.column_dimensions['B'].width = 15
    ws.column_dimensions['C'].width = 15
    ws.column_dimensions['D'].width = 15
    ws.column_dimensions['E'].width = 15

    # 表头
    headers = ['轮次(Epoch)', '训练Loss', '验证Loss', '训练Dice', '验证Dice']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        cell.border = thin_border

    # 数据行
    for epoch in range(len(history['train_loss'])):
        row = epoch + 2
        ws.cell(row=row, column=1, value=epoch + 1).border = thin_border
        ws.cell(row=row, column=2, value=round(history['train_loss'][epoch], 6)).border = thin_border
        ws.cell(row=row, column=3, value=round(history['val_loss'][epoch], 6)).border = thin_border
        ws.cell(row=row, column=4, value=round(history['train_dice'][epoch], 6)).border = thin_border
        ws.cell(row=row, column=5, value=round(history['val_dice'][epoch], 6)).border = thin_border

        # 验证Dice最高值高亮
        if history['val_dice'][epoch] == best_val_dice:
            for col in range(1, 6):
                ws.cell(row=row, column=col).fill = PatternFill(
                    start_color='C6EFCE', end_color='C6EFCE', fill_type='solid'
                )

    # 添加汇总信息sheet
    ws_summary = wb.create_sheet('训练配置与汇总')
    ws_summary.column_dimensions['A'].width = 20
    ws_summary.column_dimensions['B'].width = 15

    summary_data = [
        ('训练配置', '值'),
        ('数据集路径', config.get('dataset_path', 'N/A')),
        ('训练轮次', config.get('epochs', 30)),
        ('批次大小', config.get('batch_size', 4)),
        ('学习率', config.get('learning_rate', 1e-4)),
        ('数据集划分', '7:1:2 (训练:验证:测试)'),
        ('', ''),
        ('训练结果', '值'),
        ('最佳验证Dice', round(best_val_dice, 6)),
        ('最终验证Dice', round(history['val_dice'][-1], 6)),
        ('测试集Dice', round(test_dice, 6) if test_dice is not None else 'N/A'),
        ('训练开始时间', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
    ]

    for row_idx, (key, value) in enumerate(summary_data, 1):
        ws_summary.cell(row=row_idx, column=1, value=key).border = thin_border
        ws_summary.cell(row=row_idx, column=2, value=value).border = thin_border
        if row_idx in [1, 9]:  # 表头行
            for col in [1, 2]:
                ws_summary.cell(row=row_idx, column=col).font = header_font
                ws_summary.cell(row=row_idx, column=col).fill = header_fill

    wb.save(excel_path)
    print(f"\n📊 训练指标已保存至: {excel_path}")


def evaluate_model(model_path, dataset_path):
    # 评估阶段也必须使用与之对应的 ResNet34-UNet
    images_dir = os.path.join(dataset_path, 'images')
    masks_dir = os.path.join(dataset_path, 'masks')

    all_images = sorted(glob.glob(os.path.join(images_dir, '*')))
    all_images = [f for f in all_images if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff'))]

    dataset = MedicalDataset(all_images, masks_dir, transform=JointTransform(is_train=False))
    dataloader = DataLoader(dataset, batch_size=1, shuffle=False)

    # 实例化模型
    model = smp.Unet(
        encoder_name="resnet34",
        encoder_weights=None,           # 推理时不需要下载权重了
        in_channels=1,
        classes=1,
        activation=None
    ).to(device)

    # 加载你训练好的权重
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()

    total_dice, total_iou, total_precision, total_recall = 0.0, 0.0, 0.0, 0.0
    count = 0

    with torch.no_grad():
        for images, masks in dataloader:
            images, masks = images.to(device), masks.to(device)
            outputs = model(images)

            pred = (torch.sigmoid(outputs) > 0.5).float()
            intersection = (pred * masks).sum()

            dice = (2. * intersection + 1e-5) / (pred.sum() + masks.sum() + 1e-5)
            total_dice += dice.item()

            union = pred.sum() + masks.sum() - intersection
            iou = (intersection + 1e-5) / (union + 1e-5)
            total_iou += iou.item()

            precision = (intersection + 1e-5) / (pred.sum() + 1e-5)
            total_precision += precision.item()

            recall = (intersection + 1e-5) / (masks.sum() + 1e-5)
            total_recall += recall.item()

            count += 1

    if count == 0: count = 1

    metrics = {
        'dice': total_dice / count,
        'iou': total_iou / count,
        'precision': total_precision / count,
        'recall': total_recall / count,
        'f1': 2 * (total_precision / count) * (total_recall / count) / ((total_precision / count) + (total_recall / count) + 1e-8)
    }
    return metrics

if __name__ == '__main__':
    print("训练模块加载成功 (神级预训练+不平衡数据深度优化版本)")
