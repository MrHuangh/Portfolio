# 数据集目录

本目录用于存放训练/验证数据。

## 目录结构

```
dataset/
├── data.yaml          # 数据集配置 (由脚本自动生成)
├── images/
│   ├── train/         # 训练图片 (.jpg/.png)
│   └── val/           # 验证图片 (.jpg/.png)
├── labels/
│   ├── train/         # 训练标注 (.txt, YOLO格式)
│   └── val/           # 验证标注 (.txt, YOLO格式)
└── classes.txt        # 类别名称列表
```

## 标注格式 (YOLO)

每个图片对应一个同名 `.txt` 标注文件，每行一个目标：

```
class_id x_center y_center width height
```

- `class_id`: 类别索引 (从 0 开始)
- `x_center, y_center`: 中心点坐标 (归一化到 0~1)
- `width, height`: 宽高 (归一化到 0~1)

示例 (图片中有一个划痕和一个裂纹):
```
0 0.45 0.32 0.12 0.08
2 0.78 0.65 0.05 0.15
```

## 快速开始

```bash
# 方式一: 从原始数据自动构建
python prepare_dataset.py --source ./raw_data --classes scratch dent crack

# 方式二: 手动放置 (按上述结构放入文件即可)
# 然后校验:
python prepare_dataset.py --validate
```
