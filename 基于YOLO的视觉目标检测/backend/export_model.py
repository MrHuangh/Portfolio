"""
模型部署工具
=============================================
将训练好的 best.pt 部署到后端供 API 调用

使用方法:
    # 部署训练好的模型 (推荐)
    python export_model.py --source runs/train/defect_detect/weights/best.pt

    # 部署并重命名
    python export_model.py --source runs/train/defect_detect/weights/best.pt --name defect_v1

    # 回退到预训练模型
    python export_model.py --reset

    # 查看当前部署的模型
    python export_model.py --status
=============================================
"""

import argparse
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="YOLOv11 模型部署工具")
    parser.add_argument("--source", type=str, help="训练好的权重文件路径 (best.pt 或 last.pt)")
    parser.add_argument("--name", type=str, default="", help="部署后的模型名称 (可选)")
    parser.add_argument("--reset", action="store_true", help="回退到原始 yolo11n.pt 预训练模型")
    parser.add_argument("--status", action="store_true", help="查看当前部署状态")
    parser.add_argument("--backup", action="store_true", default=True, help="部署前自动备份当前模型")
    return parser.parse_args()


def get_model_info(model_path: Path) -> dict:
    """获取模型基本信息"""
    info = {
        "path": str(model_path),
        "exists": model_path.exists(),
        "size_mb": 0,
        "modified": "",
    }
    if model_path.exists():
        info["size_mb"] = model_path.stat().st_size / (1024 * 1024)
        info["modified"] = datetime.fromtimestamp(
            model_path.stat().st_mtime
        ).strftime("%Y-%m-%d %H:%M:%S")
    return info


def show_status():
    """显示当前模型部署状态"""
    backend_dir = Path(__file__).resolve().parent
    current_model = backend_dir / "yolo11n.pt"
    backup_dir = backend_dir / "model_backups"

    print("=" * 50)
    print("  当前模型部署状态")
    print("=" * 50)

    # 当前模型
    info = get_model_info(current_model)
    if info["exists"]:
        print(f"\n  当前模型: {current_model.name}")
        print(f"  大小:     {info['size_mb']:.1f} MB")
        print(f"  修改时间: {info['modified']}")
    else:
        print(f"\n  [警告] 模型文件不存在: {current_model}")

    # 备份列表
    if backup_dir.exists():
        backups = sorted(backup_dir.glob("*.pt"), key=lambda p: p.stat().st_mtime, reverse=True)
        if backups:
            print(f"\n  备份模型 ({len(backups)} 个):")
            for b in backups[:5]:
                b_info = get_model_info(b)
                print(f"    {b.name}  ({b_info['size_mb']:.1f} MB, {b_info['modified']})")
    else:
        print("\n  暂无备份")


def deploy_model(source: Path, name: str, backup: bool):
    """部署模型到后端"""
    backend_dir = Path(__file__).resolve().parent
    target = backend_dir / "yolo11n.pt"
    backup_dir = backend_dir / "model_backups"

    if not source.exists():
        print(f"[错误] 源权重文件不存在: {source}")
        # 尝试在 runs/train/ 下查找
        search_patterns = [
            backend_dir / "runs" / "train" / "**" / source.name,
            backend_dir / "runs" / "train" / "**" / "best.pt",
        ]
        for pattern in search_patterns:
            matches = list(backend_dir.glob(str(pattern.relative_to(backend_dir))))
            if matches:
                source = matches[0]
                print(f"[信息] 找到权重文件: {source}")
                break
        else:
            print("[错误] 未找到权重文件, 请检查训练是否完成")
            sys.exit(1)

    # 备份当前模型
    if backup and target.exists():
        backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"yolo11n_backup_{timestamp}.pt"
        shutil.copy2(target, backup_dir / backup_name)
        print(f"[备份] 当前模型已备份到: model_backups/{backup_name}")

    # 部署新模型
    shutil.copy2(source, target)
    info = get_model_info(target)

    print(f"\n[部署成功]")
    print(f"  模型文件: {target}")
    print(f"  大小:     {info['size_mb']:.1f} MB")
    print(f"\n  重启后端服务即可使用新模型:")
    print(f"    python server.py")


def reset_model():
    """回退到预训练模型"""
    backend_dir = Path(__file__).resolve().parent
    backup_dir = backend_dir / "model_backups"
    current = backend_dir / "yolo11n.pt"

    # 找到最原始的备份
    original_backup = None
    if backup_dir.exists():
        backups = sorted(backup_dir.glob("yolo11n_backup_*.pt"))
        if backups:
            original_backup = backups[0]  # 最早的备份

    if original_backup:
        shutil.copy2(original_backup, current)
        print(f"[重置] 已恢复到原始模型: {original_backup.name}")
    else:
        # 重新下载预训练模型
        print("[重置] 无备份, 重新下载 yolo11n.pt 预训练权重...")
        from ultralytics import YOLO
        model = YOLO("yolo11n.pt")  # 自动下载
        print("[重置] 下载完成")

    print("  重启后端服务生效")


def main():
    args = parse_args()

    if args.status:
        show_status()
    elif args.reset:
        reset_model()
    elif args.source:
        deploy_model(Path(args.source), args.name, args.backup)
    else:
        print("请指定操作: --source <权重路径> | --reset | --status")
        print("详细帮助: python export_model.py --help")


if __name__ == "__main__":
    main()
