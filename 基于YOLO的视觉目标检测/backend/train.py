"""
YOLOv11 微调训练脚本
=============================================
用途: 在自定义工业缺陷数据集上微调 YOLOv11 模型
环境: conda activate yolov11

使用方法:
    # 基础训练 (使用默认超参)
    python train.py

    # 指定配置训练
    python train.py --data data.yaml --epochs 100 --imgsz 640

    # 使用更大的模型 + GPU
    python train.py --model yolo11s.pt --device 0

    # 快速验证流程 (少量 epoch)
    python train.py --epochs 5 --quick
=============================================
"""

import argparse
import os
import sys
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(
        description="YOLOv11 微调训练 - 工业缺陷检测",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python train.py                                    # 默认配置训练
  python train.py --data custom_data.yaml            # 指定数据集
  python train.py --epochs 200 --batch 8             # 调参
  python train.py --model yolo11m.pt --imgsz 1280    # 大模型+大尺寸
  python train.py --quick                            # 快速验证 (5 epochs)
        """,
    )

    # ===== 模型选择 =====
    parser.add_argument(
        "--model",
        type=str,
        default="yolo11n.pt",
        help="预训练模型 (default: yolo11n.pt)\n"
        "  可选: yolo11n.pt / yolo11s.pt / yolo11m.pt / yolo11l.pt / yolo11x.pt\n"
        "  n=nano(3M) s=small(11M) m=medium(25M) l=large(46M) x=xlarge(68M)",
    )

    # ===== 数据集 =====
    parser.add_argument(
        "--data",
        type=str,
        default="data.yaml",
        help="数据集配置文件路径 (default: data.yaml)",
    )

    # ===== 训练超参 =====
    parser.add_argument("--epochs", type=int, default=100, help="训练总轮次 (default: 100)")
    parser.add_argument("--batch", type=int, default=16, help="批次大小, -1=自动 (default: 16)")
    parser.add_argument("--imgsz", type=int, default=640, help="输入图片尺寸 (default: 640)")
    parser.add_argument("--device", type=str, default="", help="训练设备, 空=自动 (default: auto)")
    parser.add_argument("--workers", type=int, default=8, help="数据加载线程数 (default: 8)")
    parser.add_argument("--patience", type=int, default=50, help="早停耐心值, 0=关闭 (default: 50)")

    # ===== 优化器参数 =====
    parser.add_argument("--optimizer", type=str, default="auto",
                        choices=["SGD", "Adam", "AdamW", "NAdam", "RAdam", "RMSProp", "auto"],
                        help="优化器 (default: auto)")
    parser.add_argument("--lr0", type=float, default=0.01, help="初始学习率 (default: 0.01)")
    parser.add_argument("--lrf", type=float, default=0.01, help="最终学习率 = lr0 * lrf (default: 0.01)")
    parser.add_argument("--momentum", type=float, default=0.937, help="SGD动量/Adam beta1 (default: 0.937)")
    parser.add_argument("--weight_decay", type=float, default=0.0005, help="L2正则化权重衰减 (default: 0.0005)")

    # ===== 数据增强 =====
    parser.add_argument("--augment", action="store_true", default=True, help="启用数据增强 (default: True)")
    parser.add_argument("--no-augment", dest="augment", action="store_false", help="关闭数据增强")
    parser.add_argument("--mosaic", type=float, default=1.0, help="Mosaic增强概率 0-1 (default: 1.0)")
    parser.add_argument("--mixup", type=float, default=0.0, help="MixUp增强概率 0-1 (default: 0.0)")
    parser.add_argument("--close-mosaic", type=int, default=10, help="最后N轮关闭Mosaic (default: 10)")
    parser.add_argument("--hsv_h", type=float, default=0.015, help="HSV色调增强 (default: 0.015)")
    parser.add_argument("--hsv_s", type=float, default=0.7, help="HSV饱和度增强 (default: 0.7)")
    parser.add_argument("--hsv_v", type=float, default=0.4, help="HSV亮度增强 (default: 0.4)")
    parser.add_argument("--flipud", type=float, default=0.0, help="上下翻转概率 (default: 0.0)")
    parser.add_argument("--fliplr", type=float, default=0.5, help="左右翻转概率 (default: 0.5)")
    parser.add_argument("--degrees", type=float, default=0.0, help="旋转角度 ± (default: 0.0)")
    parser.add_argument("--translate", type=float, default=0.1, help="平移 ± (default: 0.1)")
    parser.add_argument("--scale", type=float, default=0.5, help="缩放 ± (default: 0.5)")

    # ===== 输出控制 =====
    parser.add_argument("--project", type=str, default="runs/train", help="输出目录 (default: runs/train)")
    parser.add_argument("--name", type=str, default="defect_detect", help="实验名称 (default: defect_detect)")
    parser.add_argument("--exist-ok", action="store_true", help="覆盖已有实验目录")
    parser.add_argument("--pretrained", action="store_true", default=True, help="使用预训练权重")
    parser.add_argument("--no-pretrained", dest="pretrained", action="store_false", help="从随机权重训练")

    # ===== 快速模式 =====
    parser.add_argument("--quick", action="store_true", help="快速验证模式 (5 epochs, batch=4)")

    return parser.parse_args()


def validate_dataset(data_path: str):
    """校验数据集配置和文件完整性"""
    import yaml

    if not os.path.exists(data_path):
        print(f"[错误] 数据集配置文件不存在: {data_path}")
        print("请先准备数据集, 参考 data.yaml 中的说明")
        sys.exit(1)

    with open(data_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    base = Path(cfg.get("path", "."))
    train_img_dir = base / cfg["train"]
    val_img_dir = base / cfg["val"]

    # 检查目录是否存在
    errors = []
    if not train_img_dir.exists():
        errors.append(f"训练图片目录不存在: {train_img_dir}")
    if not val_img_dir.exists():
        errors.append(f"验证图片目录不存在: {val_img_dir}")

    if errors:
        for e in errors:
            print(f"[错误] {e}")
        print("\n请先运行数据集准备脚本:")
        print("  python prepare_dataset.py --source <图片目录> --classes <类别1> <类别2>")
        sys.exit(1)

    # 统计图片数量
    exts = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}
    train_imgs = [f for f in train_img_dir.iterdir() if f.suffix.lower() in exts]
    val_imgs = [f for f in val_img_dir.iterdir() if f.suffix.lower() in exts]

    if len(train_imgs) == 0:
        print(f"[错误] 训练集无图片: {train_img_dir}")
        sys.exit(1)

    # 检查标注文件
    train_label_dir = base / "labels" / "train"
    val_label_dir = base / "labels" / "val"
    missing_labels = 0

    for img in train_imgs[:10]:  # 抽样检查前10张
        label = train_label_dir / (img.stem + ".txt")
        if not label.exists():
            missing_labels += 1

    print(f"[数据集校验]")
    print(f"  类别数: {cfg['nc']}")
    print(f"  类别名: {cfg['names']}")
    print(f"  训练集: {len(train_imgs)} 张图片")
    print(f"  验证集: {len(val_imgs)} 张图片")
    if missing_labels > 0:
        print(f"  [警告] 抽样10张训练图片, {missing_labels}张缺少对应标注文件")

    return cfg


def main():
    args = parse_args()

    # 快速模式覆盖
    if args.quick:
        args.epochs = 5
        args.batch = 4
        args.workers = 2
        args.patience = 3
        print("[快速验证模式] epochs=5, batch=4")

    print("=" * 60)
    print("  YOLOv11 微调训练 - 工业缺陷检测")
    print("=" * 60)

    # 切换到脚本所在目录 (backend/)
    script_dir = Path(__file__).resolve().parent
    os.chdir(script_dir)

    # 校验数据集
    cfg = validate_dataset(args.data)

    # 设备检测
    import torch
    if args.device:
        device = args.device
    elif torch.cuda.is_available():
        device = "0"
        gpu_name = torch.cuda.get_device_name(0)
        vram = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        print(f"[GPU] {gpu_name} ({vram:.1f} GB)")
    else:
        device = "cpu"
        print("[设备] CPU (训练较慢, 建议使用GPU)")

    print(f"\n[训练配置]")
    print(f"  模型:     {args.model}")
    print(f"  数据集:   {args.data}")
    print(f"  轮次:     {args.epochs}")
    print(f"  批次:     {args.batch}")
    print(f"  图片尺寸: {args.imgsz}")
    print(f"  优化器:   {args.optimizer}")
    print(f"  初始学习率: {args.lr0}")
    print(f"  设备:     {device}")
    print(f"  数据增强: {'开启' if args.augment else '关闭'}")
    print(f"  输出目录: {args.project}/{args.name}")
    print()

    # ===== 开始训练 =====
    from ultralytics import YOLO

    # 加载预训练模型
    model = YOLO(args.model)

    # 训练
    results = model.train(
        # --- 数据 ---
        data=args.data,
        imgsz=args.imgsz,
        batch=args.batch,
        # --- 训练策略 ---
        epochs=args.epochs,
        patience=args.patience,
        device=device,
        workers=args.workers,
        pretrained=args.pretrained,
        # --- 优化器 ---
        optimizer=args.optimizer,
        lr0=args.lr0,
        lrf=args.lrf,
        momentum=args.momentum,
        weight_decay=args.weight_decay,
        # --- 数据增强 ---
        augment=args.augment,
        mosaic=args.mosaic,
        mixup=args.mixup,
        close_mosaic=args.close_mosaic,
        hsv_h=args.hsv_h,
        hsv_s=args.hsv_s,
        hsv_v=args.hsv_v,
        flipud=args.flipud,
        fliplr=args.fliplr,
        degrees=args.degrees,
        translate=args.translate,
        scale=args.scale,
        # --- 输出 ---
        project=args.project,
        name=args.name,
        exist_ok=args.exist_ok,
    )

    # ===== 训练完成 =====
    best_weights = Path(args.project) / args.name / "weights" / "best.pt"
    last_weights = Path(args.project) / args.name / "weights" / "last.pt"

    print("\n" + "=" * 60)
    print("  训练完成!")
    print("=" * 60)
    print(f"  最佳权重: {best_weights}")
    print(f"  最终权重: {last_weights}")
    print(f"  训练日志: {args.project}/{args.name}/")
    print()
    print("  下一步:")
    print(f"    1. 查看训练曲线: {args.project}/{args.name}/results.csv")
    print(f"    2. 查看混淆矩阵: {args/project}/{args.name}/confusion_matrix.png")
    print(f"    3. 部署模型:     python export_model.py --source {best_weights}")
    print()


if __name__ == "__main__":
    main()
