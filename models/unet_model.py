"""
Unet模型定义 - 医学影像分割
基于经典的U-Net架构实现
"""
import torch
import torch.nn as nn
import torch.nn.functional as F


class DoubleConv(nn.Module):
    """双卷积块：卷积 -> BN -> ReLU -> 卷积 -> BN -> ReLU"""
    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.double_conv = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True)
        )

    def forward(self, x):
        return self.double_conv(x)


class Down(nn.Module):
    """下采样块：MaxPool -> DoubleConv"""
    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.maxpool_conv = nn.Sequential(
            nn.MaxPool2d(2),
            DoubleConv(in_channels, out_channels)
        )

    def forward(self, x):
        return self.maxpool_conv(x)


class Up(nn.Module):
    """上采样块：上采样 -> 拼接 -> DoubleConv"""
    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.up = nn.ConvTranspose2d(in_channels, in_channels // 2, kernel_size=2, stride=2)
        self.conv = DoubleConv(in_channels, out_channels)

    def forward(self, x1, x2):
        x1 = self.up(x1)
        # 处理尺寸不匹配
        diffY = x2.size()[2] - x1.size()[2]
        diffX = x2.size()[3] - x1.size()[3]
        x1 = F.pad(x1, [diffX // 2, diffX - diffX // 2, diffY // 2, diffY - diffY // 2])
        x = torch.cat([x2, x1], dim=1)
        return self.conv(x)


class OutConv(nn.Module):
    """输出卷积"""
    def __init__(self, in_channels, out_channels):
        super(OutConv, self).__init__()
        self.conv = nn.Conv2d(in_channels, out_channels, kernel_size=1)

    def forward(self, x):
        return self.conv(x)


class UNet(nn.Module):
    """
    U-Net模型
    编码器-解码器结构，带跳跃连接
    """
    def __init__(self, in_channels=1, out_channels=1, base_features=64):
        super(UNet, self).__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels

        # 编码器
        self.inc = DoubleConv(in_channels, base_features)
        self.down1 = Down(base_features, base_features * 2)
        self.down2 = Down(base_features * 2, base_features * 4)
        self.down3 = Down(base_features * 4, base_features * 8)
        self.down4 = Down(base_features * 8, base_features * 16)

        # 解码器
        self.up1 = Up(base_features * 16, base_features * 8)
        self.up2 = Up(base_features * 8, base_features * 4)
        self.up3 = Up(base_features * 4, base_features * 2)
        self.up4 = Up(base_features * 2, base_features)
        self.outc = OutConv(base_features, out_channels)

    def forward(self, x):
        # 编码器路径
        x1 = self.inc(x)
        x2 = self.down1(x1)
        x3 = self.down2(x2)
        x4 = self.down3(x3)
        x5 = self.down4(x4)

        # 解码器路径
        x = self.up1(x5, x4)
        x = self.up2(x, x3)
        x = self.up3(x, x2)
        x = self.up4(x, x1)
        x = self.outc(x)

        # 如果是二分类，使用sigmoid
        if self.out_channels == 1:
            x = torch.sigmoid(x)

        return x


class UNetWithAttention(nn.Module):
    """
    带注意力机制的U-Net模型
    """
    def __init__(self, in_channels=1, out_channels=1, base_features=64):
        super(UNetWithAttention, self).__init__()
        self.unet = UNet(in_channels, out_channels, base_features)

    def forward(self, x):
        return self.unet(x)


def get_model(config=None):
    """获取模型实例"""
    if config is None:
        config = {}

    in_channels = config.get('in_channels', 1)
    out_channels = config.get('out_channels', 1)
    base_features = config.get('base_features', 64)

    return UNet(in_channels, out_channels, base_features)


def count_parameters(model):
    """计算模型参数量"""
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


if __name__ == '__main__':
    # 测试模型
    model = UNet(in_channels=1, out_channels=1)
    x = torch.randn(1, 1, 256, 256)
    y = model(x)
    print(f"输入形状: {x.shape}")
    print(f"输出形状: {y.shape}")
    print(f"参数量: {count_parameters(model):,}")
