"""
数据集准备工具
=============================================
功能:
  1. 从 YOLO 格式的标注数据中自动构建训练/验证集
  2. 支持从 VOC XML / YOLO txt / COCO JSON 格式转换
  3. 自动按比例划分 train/val
  4. 标注格式校验
  5. 数据集统计报告

使用方法:
    # 从 YOLO 格式标注构建数据集
    python prepare_dataset.py --source ./raw_data --format yolo --classes scratch dent crack

    # 从 VOC XML 格式转换
    python prepare_dataset.py --source ./raw_data --format voc --classes scratch dent crack

    # 自定义 train/val 比例
    python prepare_dataset.py --source ./raw_data --format yolo --val-ratio 0.2

    # 仅校验现有数据集
    python prepare_dataset.py --validate
=============================================
"""

import argparse
import os
import random
import shutil
import sys
from collections import defaultdict
from pathlib import Path


# 支持的图片格式
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}


def parse_args():
    parser = argparse.ArgumentParser(description="YOLO 数据集准备工具")

    # 模式选择
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--source", type=str, help="原始数据目录 (包含图片和标注)")
    mode.add_argument("--validate", action="store_true", help="仅校验现有数据集")

    # 标注格式
    parser.add_argument("--format", type=str, default="yolo",
                        choices=["yolo", "voc", "coco"],
                        help="标注格式 (default: yolo)")

    # 类别
    parser.add_argument("--classes", nargs="+", type=str, default=None,
                        help="类别名称列表, 例如: --classes scratch dent crack")

    # 划分参数
    parser.add_argument("--val-ratio", type=float, default=0.2, help="验证集比例 (default: 0.2)")
    parser.add_argument("--seed", type=int, default=42, help="随机种子 (default: 42)")

    # 目标目录
    parser.add_argument("--target", type=str, default="dataset", help="目标数据集目录 (default: dataset)")

    # 标注子目录名
    parser.add_argument("--label-dir", type=str, default="labels",
                        help="标注文件子目录名 (default: labels)")

    return parser.parse_args()


def collect_images(directory: Path) -> list[Path]:
    """收集目录下所有图片文件"""
    images = []
    for f in sorted(directory.iterdir()):
        if f.is_file() and f.suffix.lower() in IMAGE_EXTS:
            images.append(f)
    return images


def validate_yolo_label(label_path: Path, num_classes: int) -> list[str]:
    """
    校验单个 YOLO 标注文件
    格式: class_id x_center y_center width height (每行一个, 归一化坐标)
    返回错误信息列表, 空=合法
    """
    errors = []
    if not label_path.exists():
        return [f"标注文件不存在: {label_path}"]

    with open(label_path, "r") as f:
        lines = f.readlines()

    for i, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) != 5:
            errors.append(f"行{i}: 需要5个值 (class cx cy w h), 实际有{len(parts)}个")
            continue

        try:
            cls_id = int(parts[0])
            coords = [float(x) for x in parts[1:]]
        except ValueError:
            errors.append(f"行{i}: 格式错误 '{line}'")
            continue

        if cls_id < 0 or cls_id >= num_classes:
            errors.append(f"行{i}: class_id={cls_id} 超出范围 [0, {num_classes - 1}]")

        for j, c in enumerate(coords):
            if j < 2:  # cx, cy
                if c < 0 or c > 1:
                    errors.append(f"行{i}: 坐标值 {c} 超出 [0, 1] 范围")
            else:  # w, h
                if c <= 0 or c > 1:
                    errors.append(f"行{i}: 尺寸值 {c} 超出 (0, 1] 范围")

    return errors


def convert_voc_to_yolo(xml_path: Path, class_map: dict[str, int]) -> str:
    """
    将单个 VOC XML 标注转换为 YOLO 格式字符串
    class_map: {"scratch": 0, "dent": 1, ...}
    """
    import xml.etree.ElementTree as ET

    tree = ET.parse(xml_path)
    root = tree.getroot()

    size = root.find("size")
    img_w = int(size.find("width").text)
    img_h = int(size.find("height").text)

    lines = []
    for obj in root.findall("object"):
        cls_name = obj.find("name").text.strip()
        if cls_name not in class_map:
            continue

        bbox = obj.find("bndbox")
        xmin = float(bbox.find("xmin").text)
        ymin = float(bbox.find("ymin").text)
        xmax = float(bbox.find("xmax").text)
        ymax = float(bbox.find("ymax").text)

        # 转换为 YOLO 格式 (归一化中心坐标 + 宽高)
        x_center = (xmin + xmax) / 2 / img_w
        y_center = (ymin + ymax) / 2 / img_h
        width = (xmax - xmin) / img_w
        height = (ymax - ymin) / img_h

        cls_id = class_map[cls_name]
        lines.append(f"{cls_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}")

    return "\n".join(lines)


def convert_coco_to_yolo(coco_json_path: Path, class_map: dict[str, int]) -> dict[str, str]:
    """
    将 COCO JSON 标注转换为 YOLO 格式
    返回 {image_filename_stem: yolo_label_string}
    """
    import json

    with open(coco_json_path, "r", encoding="utf-8") as f:
        coco = json.load(f)

    # 建立 category_id -> class_id 映射
    cat_id_map = {}
    for cat in coco["categories"]:
        if cat["name"] in class_map:
            cat_id_map[cat["id"]] = class_map[cat["name"]]

    # 建立 image_id -> image_info 映射
    img_map = {}
    for img in coco["images"]:
        img_map[img["id"]] = img

    # 按图片收集标注
    annotations_by_img = defaultdict(list)
    for ann in coco["annotations"]:
        if ann["category_id"] in cat_id_map:
            annotations_by_img[ann["image_id"]].append(ann)

    result = {}
    for img_id, anns in annotations_by_img.items():
        img_info = img_map[img_id]
        img_w = img_info["width"]
        img_h = img_info["height"]
        stem = Path(img_info["file_name"]).stem

        lines = []
        for ann in anns:
            cls_id = cat_id_map[ann["category_id"]]
            # COCO bbox: [x, y, width, height] (左上角)
            x, y, w, h = ann["bbox"]
            x_center = (x + w / 2) / img_w
            y_center = (y + h / 2) / img_h
            norm_w = w / img_w
            norm_h = h / img_h
            lines.append(f"{cls_id} {x_center:.6f} {y_center:.6f} {norm_w:.6f} {norm_h:.6f}")

        result[stem] = "\n".join(lines)

    return result


def build_dataset(args):
    """构建训练/验证数据集"""
    source = Path(args.source)
    target = Path(args.target)

    if not source.exists():
        print(f"[错误] 源目录不存在: {source}")
        sys.exit(1)

    # 确定类别
    if args.classes:
        classes = args.classes
    else:
        # 尝试从 classes.txt 读取
        cls_file = source / "classes.txt"
        if cls_file.exists():
            classes = [l.strip() for l in cls_file.read_text().splitlines() if l.strip()]
            print(f"[信息] 从 classes.txt 读取类别: {classes}")
        else:
            print("[错误] 请通过 --classes 指定类别名称")
            print("  例如: --classes scratch dent crack")
            sys.exit(1)

    class_map = {name: i for i, name in enumerate(classes)}
    nc = len(classes)

    print(f"[数据集准备]")
    print(f"  源目录:   {source}")
    print(f"  格式:     {args.format}")
    print(f"  类别({nc}): {classes}")
    print(f"  验证比例: {args.val_ratio}")
    print()

    # ===== 收集图片和标注 =====
    # 查找图片目录
    img_dir = None
    for candidate in ["images", "img", "JPEGImages", ""]:
        c = source / candidate if candidate else source
        if c.exists() and any(p.suffix.lower() in IMAGE_EXTS for p in c.iterdir()):
            img_dir = c
            break

    if img_dir is None:
        print(f"[错误] 未找到图片文件: {source}")
        sys.exit(1)

    # 查找标注目录
    label_dir = None
    for candidate in [args.label_dir, "labels", "Annotations", ""]:
        c = source / candidate if candidate else source
        if c.exists():
            txt_files = list(c.glob("*.txt"))
            xml_files = list(c.glob("*.xml"))
            if txt_files or xml_files:
                label_dir = c
                break

    images = collect_images(img_dir)
    print(f"  找到 {len(images)} 张图片")

    if len(images) == 0:
        print("[错误] 未找到图片文件")
        sys.exit(1)

    # ===== 校验标注 =====
    print("\n[校验标注文件...]")
    valid_pairs = []  # (image_path, label_content)
    error_count = 0
    missing_label_count = 0

    for img_path in images:
        stem = img_path.stem

        if args.format == "yolo":
            # YOLO txt 标注
            lbl = label_dir / (stem + ".txt") if label_dir else img_dir / (stem + ".txt")
            if lbl.exists():
                errors = validate_yolo_label(lbl, nc)
                if errors:
                    error_count += 1
                    for e in errors[:3]:  # 每个文件最多报3个错误
                        print(f"  [!] {lbl.name}: {e}")
                else:
                    content = lbl.read_text(encoding="utf-8").strip()
                    if content:
                        valid_pairs.append((img_path, content))
                    else:
                        missing_label_count += 1
            else:
                missing_label_count += 1

        elif args.format == "voc":
            xml = label_dir / (stem + ".xml") if label_dir else img_dir / (stem + ".xml")
            if xml.exists():
                yolo_content = convert_voc_to_yolo(xml, class_map)
                if yolo_content.strip():
                    valid_pairs.append((img_path, yolo_content))
                else:
                    missing_label_count += 1
            else:
                missing_label_count += 1

    if args.format == "coco":
        coco_json = None
        for candidate in ["annotations.json", "instances.json", "result.json"]:
            c = source / candidate
            if c.exists():
                coco_json = c
                break
        if coco_json is None:
            print("[错误] 未找到 COCO JSON 标注文件")
            sys.exit(1)

        coco_labels = convert_coco_to_yolo(coco_json, class_map)
        for img_path in images:
            stem = img_path.stem
            if stem in coco_labels and coco_labels[stem].strip():
                valid_pairs.append((img_path, coco_labels[stem]))

    print(f"  有效标注: {len(valid_pairs)}")
    print(f"  缺少标注: {missing_label_count}")
    print(f"  标注错误: {error_count}")

    if len(valid_pairs) == 0:
        print("\n[错误] 没有可用的标注数据")
        sys.exit(1)

    # ===== 划分 train/val =====
    random.seed(args.seed)
    random.shuffle(valid_pairs)

    val_count = max(1, int(len(valid_pairs) * args.val_ratio))
    val_pairs = valid_pairs[:val_count]
    train_pairs = valid_pairs[val_count:]

    print(f"\n[划分结果]")
    print(f"  训练集: {len(train_pairs)} 张")
    print(f"  验证集: {len(val_pairs)} 张")

    # ===== 复制文件 =====
    dataset = Path(args.target)

    for split_name, pairs in [("train", train_pairs), ("val", val_pairs)]:
        img_out = dataset / "images" / split_name
        lbl_out = dataset / "labels" / split_name
        img_out.mkdir(parents=True, exist_ok=True)
        lbl_out.mkdir(parents=True, exist_ok=True)

        for img_path, label_content in pairs:
            # 复制图片
            dst_img = img_out / img_path.name
            if not dst_img.exists():
                shutil.copy2(img_path, dst_img)

            # 写入标注
            dst_lbl = lbl_out / (img_path.stem + ".txt")
            dst_lbl.write_text(label_content, encoding="utf-8")

    # ===== 生成 data.yaml =====
    data_yaml = dataset / "data.yaml"
    yaml_content = f"""# 自动生成的数据集配置
# 生成时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

path: ./{dataset.name}
train: images/train
val: images/val

nc: {nc}
names:
"""
    for i, name in enumerate(classes):
        yaml_content += f"  {i}: {name}\n"

    data_yaml.write_text(yaml_content, encoding="utf-8")

    # ===== 统计报告 =====
    print(f"\n[类别统计]")
    class_counts = defaultdict(int)
    for _, content in valid_pairs:
        for line in content.splitlines():
            parts = line.strip().split()
            if parts:
                cls_id = int(parts[0])
                if 0 <= cls_id < nc:
                    class_counts[cls_id] += 1

    for i, name in enumerate(classes):
        count = class_counts.get(i, 0)
        bar = "█" * min(count, 50)
        print(f"  {name:>12}: {count:>5} 个标注  {bar}")

    print(f"\n[完成]")
    print(f"  数据集目录: {dataset.resolve()}")
    print(f"  配置文件:   {data_yaml.resolve()}")
    print(f"\n  下一步: python train.py --data {data_yaml}")


def validate_existing_dataset():
    """校验现有数据集"""
    import yaml

    data_yaml = Path("data.yaml")
    if not data_yaml.exists():
        print("[错误] 未找到 data.yaml")
        sys.exit(1)

    with open(data_yaml, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    base = Path(cfg.get("path", "."))
    nc = cfg["nc"]
    names = cfg["names"]

    print(f"[数据集校验] {data_yaml}")
    print(f"  类别数: {nc}")
    print(f"  类别名: {names}")

    for split in ["train", "val"]:
        img_dir = base / cfg[split]
        lbl_dir = base / "labels" / split

        if not img_dir.exists():
            print(f"\n  [错误] {img_dir} 不存在")
            continue

        images = collect_images(img_dir)
        has_label = 0
        no_label = 0
        error_labels = 0
        class_counts = defaultdict(int)

        for img in images:
            lbl = lbl_dir / (img.stem + ".txt")
            if not lbl.exists():
                no_label += 1
                continue

            errors = validate_yolo_label(lbl, nc)
            if errors:
                error_labels += 1
                for e in errors[:2]:
                    print(f"    {lbl.name}: {e}")
            else:
                has_label += 1
                content = lbl.read_text(encoding="utf-8").strip()
                for line in content.splitlines():
                    parts = line.split()
                    if parts:
                        class_counts[int(parts[0])] += 1

        print(f"\n  [{split}] 图片: {len(images)}, 有标注: {has_label}, "
              f"缺标注: {no_label}, 标注错误: {error_labels}")
        for i in range(nc):
            print(f"    {names[i]}: {class_counts.get(i, 0)}")

    print("\n[校验完成]")


def main():
    args = parse_args()

    if args.validate:
        validate_existing_dataset()
    else:
        build_dataset(args)


if __name__ == "__main__":
    main()
