"""
Unet模型推理服务
提供图像分割接口
"""
import os
import torch
import numpy as np
from PIL import Image
import io
import base64
import json
import torchvision.transforms as transforms

# 引入强大的预训练模型库
import segmentation_models_pytorch as smp

# 模型缓存
model_cache = {}
model_device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# 默认图像预处理
transform = transforms.Compose([
    transforms.Resize((256, 256)),
    transforms.ToTensor(),
])

def get_model():
    """获取并实例化新的 ResNet34-UNet 模型"""
    model = smp.Unet(
        encoder_name="resnet34",
        encoder_weights=None,           # 推理时不需要下载 Imagenet 预训练权重
        in_channels=1,
        classes=1,
        activation=None                 # 输出 Logits，后处理时应用 Sigmoid
    )
    return model

def load_model(model_id, model_path=None):
    """加载模型"""
    if model_id in model_cache:
        return model_cache[model_id]

    model = get_model()

    if model_path and os.path.exists(model_path):
        # 加上 weights_only=True 消除 PyTorch 安全警告
        state_dict = torch.load(model_path, map_location=model_device, weights_only=True)
        model.load_state_dict(state_dict)

    model = model.to(model_device)
    model.eval()

    model_cache[model_id] = model
    return model


def preprocess_image(image_data):
    """预处理图像"""
    if isinstance(image_data, str):
        # 文件路径
        img = Image.open(image_data)
    elif isinstance(image_data, bytes):
        # 字节数据
        img = Image.open(io.BytesIO(image_data))
    else:
        return None

    # 强制转换为灰度图 (因为我们的模型 in_channels=1)
    if img.mode != 'L':
        img = img.convert('L')

    # 应用变换
    img_tensor = transform(img)

    # 增加batch维度
    img_tensor = img_tensor.unsqueeze(0)

    return img_tensor.to(model_device)


def postprocess_mask(mask_tensor, original_size=None):
    """后处理掩膜"""
    mask = mask_tensor.squeeze().cpu().detach().numpy()

    # 归一化到0-255 (经过 sigmoid 和 >0.5 之后，tensor已经是 0.0 或 1.0)
    mask = (mask * 255).astype(np.uint8)

    # 调整回原始尺寸
    if original_size:
        # 使用最近邻插值保持边缘清晰
        mask_img = Image.fromarray(mask).resize(original_size, Image.NEAREST)
        mask = np.array(mask_img)

    return mask


def save_mask(mask, save_path):
    """保存掩膜"""
    mask_img = Image.fromarray(mask)
    mask_img.save(save_path)


def mask_to_base64(mask):
    """将掩膜转换为base64"""
    mask_img = Image.fromarray(mask)
    buffered = io.BytesIO()
    mask_img.save(buffered, format='PNG')
    return base64.b64encode(buffered.getvalue()).decode()


def inference(image_data, model_id=None, model_path=None):
    """
    执行推理

    Args:
        image_data: 图像数据 (路径、字节或PIL Image)
        model_id: 模型ID
        model_path: 模型权重路径

    Returns:
        dict: 包含掩膜的字典
    """
    # 加载模型
    model = load_model(model_id, model_path)

    # 预处理
    img_tensor = preprocess_image(image_data)
    if img_tensor is None:
        return {'success': False, 'error': '图像预处理失败'}

    # 推理
    with torch.no_grad():
        output = model(img_tensor)
        # 【重要】将 Logits 转换为概率，并进行二值化
        probs = torch.sigmoid(output)
        preds = (probs > 0.5).float()

    # 后处理
    mask = postprocess_mask(preds)

    return {
        'success': True,
        'mask': mask
    }


def batch_inference(images, model_id=None, model_path=None):
    """批量推理"""
    model = load_model(model_id, model_path)
    results = []

    for image_data in images:
        result = inference(image_data, model_id, model_path)
        results.append(result)

    return results


def get_model_info(model_path=None):
    """获取模型信息"""
    info = {
        'device': str(model_device),
        'cuda_available': torch.cuda.is_available()
    }

    if model_path and os.path.exists(model_path):
        # 加上 weights_only=True
        state_dict = torch.load(model_path, map_location='cpu', weights_only=True)
        info['loaded'] = True
        info['parameters'] = sum(p.numel() for p in state_dict.values())

    return info


# 测试
if __name__ == '__main__':
    print(f"模型设备: {model_device}")
    print(f"CUDA可用: {torch.cuda.is_available()}")

    # 测试模型
    model = get_model().to(model_device)
    x = torch.randn(1, 1, 256, 256).to(model_device)
    y = model(x)
    print(f"测试输出形状: {y.shape}")
